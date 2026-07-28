#!/usr/bin/env python3
"""Prova di isolamento — lo strumento di misura di D27, e cio' che sa dire.

    python3 tools/load/prova_isolamento.py --db nli_test --utenti 20

**Che cosa misura D27.** RA3 riguarda l'ERP, non il livello conversazionale, quindi
la prova che conta misura l'impatto su chi il prodotto **non** lo sta usando (`05`
§7.1): con N utenti conversazionali attivi in modo continuativo, il tempo di risposta
di Odoo per un utente ordinario — che apre una fattura, salva un ordine, cerca un
cliente — non deve peggiorare in modo misurabile.

**Che cosa misura questo strumento.** Tre distribuzioni di latenza, tutte via HTTP,
perche' il meccanismo del guasto e' l'occupazione dei worker e una misura fatta
dentro il processo non lo toccherebbe:

1. **riferimento** — un utente ordinario, a vuoto: `search_read` su `res.partner`;
2. **sotto carico** — lo stesso, mentre N connessioni accettano turni in continuo;
3. **accettazione** — la latenza del percorso di §3.2, che deve restare attorno ai
   10 ms: e' la terza soglia di §6.1 (accettazione P95 <= 50 ms) ed e' l'indicatore
   che scatta per primo se D20a viene rotta.

**Che cosa questo strumento NON dimostra, e va detto prima dei numeri.** La
generazione del carico si ferma all'accettazione: i turni entrano in coda e il
dispatcher li elabora con il profilo attivo, quindi senza un profilo qualificato la
fase di interpretazione — che e' la quota dominante del tempo e la ragione per cui
l'esecuzione asincrona esiste — **non viene esercitata**. Il rapporto lo dichiara in
testa a ogni esecuzione anziche' in fondo.

Restano inoltre due condizioni dell'ambiente che nessuno strumento puo' correggere e
che il rapporto stampa insieme ai numeri: la modalita' di esecuzione di Odoo (con
`--workers=0` non esiste il pool prefork la cui saturazione **e'** RA3) e la
consistenza della banca dati. Una misura su un portatile con un database vuoto non e'
un'installazione rappresentativa, e chiamarla «prova superata» sarebbe falso.
"""

from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
import urllib.error
import urllib.request

DEFAULT_URL = "http://localhost:8069"


class Session:
    """Una sessione Odoo autenticata, sul trasporto che i worker servono."""

    def __init__(self, base_url: str, db: str, login: str, password: str,
                 timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor())
        self.uid = self._call("/web/session/authenticate", {
            "db": db, "login": login, "password": password})["uid"]

    def _call(self, path: str, params: dict):
        payload = json.dumps({
            "jsonrpc": "2.0", "method": "call", "params": params,
        }).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path, data=payload,
            headers={"Content-Type": "application/json"})
        with self.opener.open(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        if "error" in body:
            raise RuntimeError(json.dumps(body["error"].get("data", body["error"]))[:400])
        return body["result"]

    def call_kw(self, model: str, method: str, args, kwargs=None):
        return self._call("/web/dataset/call_kw", {
            "model": model, "method": method, "args": args,
            "kwargs": kwargs or {},
        })


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
    return ordered[index]


def report(name: str, samples: list[float]) -> str:
    if not samples:
        return f"  {name:<24} nessun campione"
    return (f"  {name:<24} n={len(samples):<5} "
            f"P50 {percentile(samples, 0.50) * 1000:7.1f} ms   "
            f"P95 {percentile(samples, 0.95) * 1000:7.1f} ms   "
            f"max {max(samples) * 1000:7.1f} ms")


def erp_probe(session: Session) -> float:
    """Una domanda che un utente ordinario fa cento volte al giorno."""
    started = time.monotonic()
    session.call_kw("res.partner", "search_read",
                    [[], ["name", "city"]], {"limit": 80})
    return time.monotonic() - started


class Load:
    """N utenti conversazionali che scrivono a ritmo umano, non a ciclo stretto.

    Il ritmo e' un parametro della prova, non un dettaglio: **L5 limita un utente a
    venti richieste al minuto**, quindi un ciclo senza pause misura il rifiuto per
    frequenza e nient'altro. Una persona che conversa con l'ERP scrive una frase ogni
    pochi secondi, ed e' quel carico che §7.2 chiama «venti utenti conversazionali
    continui».
    """

    def __init__(self, sessions: list[Session], utterance: str, pause: float = 3.0):
        self.sessions = sessions
        self.utterance = utterance
        self.pause = pause
        self.stop = threading.Event()
        self.latencies: list[float] = []
        self.refusals: dict[str, int] = {}
        self._lock = threading.Lock()

    def _loop(self, session: Session):
        interrogation = session.call_kw("nli.interrogation", "create", [{}])
        while not self.stop.is_set():
            started = time.monotonic()
            try:
                outcome = session.call_kw(
                    "nli.queue.item", "accept_request",
                    [interrogation, self.utterance])
            except Exception as error:  # noqa: BLE001 — la misura non deve morire
                # Il messaggio, non il tipo: un rifiuto per carico e un guasto di
                # configurazione si distinguono solo leggendolo, e uno strumento che
                # li confonde fa concludere la cosa sbagliata.
                outcome = {"accepted": False,
                           "reason": f"{type(error).__name__}: {str(error)[:120]}"}
            elapsed = time.monotonic() - started
            with self._lock:
                self.latencies.append(elapsed)
                if not outcome.get("accepted"):
                    reason = outcome.get("reason", "?")
                    self.refusals[reason] = self.refusals.get(reason, 0) + 1
            self.stop.wait(self.pause)

    def run(self, seconds: float):
        threads = [threading.Thread(target=self._loop, args=(session,), daemon=True)
                   for session in self.sessions]
        for thread in threads:
            thread.start()
        return threads


LOAD_PASSWORD = "aida-load-probe"


def provision_users(observer: Session, count: int) -> list[str]:
    """N utenti distinti, perche' i limiti sono per utente e per sessione.

    Con un solo accesso ripetuto N volte si misurerebbe L1 e L5 su una persona
    sola: esattamente il carico che il prodotto e' progettato per rifiutare, e non
    quello che la prova deve produrre.
    """
    # `env.ref` non esiste via RPC e i metodi privati non sono chiamabili: il
    # gruppo si ottiene dalla sua riga in `ir.model.data`, che e' un dato.
    group = observer.call_kw("ir.model.data", "search_read", [
        [["module", "=", "base"], ["name", "=", "group_user"]], ["res_id"]])[0]["res_id"]
    logins = []
    for index in range(count):
        login = f"aida_load_{index}"
        existing = observer.call_kw("res.users", "search",
                                    [[["login", "=", login]]])
        if not existing:
            observer.call_kw("res.users", "create", [{
                "name": f"AIDA load {index}", "login": login,
                "password": LOAD_PASSWORD,
                "groups_id": [(6, 0, [group])],
            }])
        else:
            observer.call_kw("res.users", "write",
                             [existing, {"password": LOAD_PASSWORD}])
        logins.append(login)
    return logins


def environment_lines() -> list[str]:
    """La modalita' di esecuzione, letta dalla configurazione dello stack.

    Non e' un dettaglio da nota a pie' di pagina: con `--workers=0` Odoo serve le
    richieste con thread dentro un solo processo, e il pool prefork la cui
    saturazione **e'** RA3 non esiste. Una misura fatta li' dice qualcosa sul
    prodotto e nulla sul rischio.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    mode = "dev"
    env_file = root / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            if line.startswith("DEPLOY_MODE="):
                mode = line.split("=", 1)[1].strip()
    override = root / f"docker-compose.{mode}.yml"
    flags = []
    if override.is_file():
        for line in override.read_text().splitlines():
            stripped = line.strip().lstrip("- ")
            if stripped.startswith("--workers") or stripped.startswith("--max-cron-threads"):
                flags.append(stripped)
    return [
        f"modalita' dello stack  {mode}",
        "flag di esecuzione     " + (", ".join(flags) or "nessuno (workers=0, threaded)"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--db", required=True)
    parser.add_argument("--login", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--utenti", type=int, default=20,
                        help="connessioni conversazionali continue (§7.2: 20)")
    parser.add_argument("--secondi", type=float, default=20.0)
    parser.add_argument("--pausa", type=float, default=3.0,
                        help="secondi fra una frase e la successiva, per utente. "
                             "A zero si misura L5, non l'isolamento")
    parser.add_argument("--frase", default="mostrami le aziende di Milano")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="secondi oltre i quali una chiamata e' considerata "
                             "persa. Una chiamata che attende due minuti non e' "
                             "una latenza alta: e' un utente che se n'e' andato")
    arguments = parser.parse_args()

    observer = Session(arguments.url, arguments.db, arguments.login,
                       arguments.password, timeout=arguments.timeout)

    print("Prova di isolamento — D27, 05 §7.1")
    print()
    print("  ambiente")
    for line in environment_lines():
        print(f"    {line}")
    partners = observer.call_kw("res.partner", "search_count", [[]])
    print(f"    res.partner nel db     {partners}")
    profiles = observer.call_kw("nli.profile", "search_count",
                                [[["state", "=", "active"]]])
    print(f"    profili attivi         {profiles}"
          + ("   <- l'interpretazione non viene esercitata" if not profiles else ""))
    print()

    baseline = [erp_probe(observer) for _ in range(40)]

    logins = provision_users(observer, arguments.utenti)
    sessions = [
        Session(arguments.url, arguments.db, login, LOAD_PASSWORD,
                timeout=arguments.timeout)
        for login in logins
    ]
    load = Load(sessions, arguments.frase, pause=arguments.pausa)
    threads = load.run(arguments.secondi)

    time.sleep(1.0)  # il carico entra a regime prima di misurare l'ERP
    under_load = []
    deadline = time.monotonic() + arguments.secondi
    while time.monotonic() < deadline:
        under_load.append(erp_probe(observer))
    load.stop.set()
    for thread in threads:
        thread.join(timeout=30)

    depth = observer.call_kw("nli.queue.item", "search_count",
                            [[["state", "=", "pending"]]])

    print("  latenza dell'utente ordinario")
    print(report("riferimento", baseline))
    print(report("sotto carico", under_load))
    print()
    print("  percorso di accettazione (05 §3.2)")
    print(report("accettazione", load.latencies))
    if load.refusals:
        print("    rifiuti: " + ", ".join(
            f"{reason} x{count}" for reason, count in sorted(load.refusals.items())))
    print()
    print(f"  coda residua (pending)   {depth}")
    print()

    base_p95 = percentile(baseline, 0.95)
    load_p95 = percentile(under_load, 0.95)
    if base_p95 > 0:
        print(f"  degrado P95 dell'ERP     {(load_p95 / base_p95 - 1) * 100:+.1f}%")
    print()
    print("  Questa esecuzione NON e' la prova di D27. La fase di interpretazione")
    print("  e' esercitata solo se esiste un profilo attivo, e l'installazione")
    print("  dev di questo repository gira senza pool prefork: la saturazione dei")
    print("  worker, che e' il meccanismo di RA3, non e' riproducibile qui.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
