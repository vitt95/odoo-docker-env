#!/usr/bin/env python3
"""
Generatore del corpus fondativo sintetico.

Principio: si genera prima lo **Stato di Interrogazione atteso**, poi lo si
verbalizza in italiano. L'interpretazione attesa e' quindi corretta per
costruzione e non richiede annotazione umana — che e' l'unico modo di produrre
un corpus senza clienti pilota (cfr. 11-corpus-fondativo.md §4.1).

Cio' che questo corpus NON e': linguaggio osservato. Non sostituisce il corpus
sigillato di D42 e non chiude il cancello di D49.

Uso:
    python3 genera_corpus.py --n 600 --seme 42 --out corpus_fondativo.jsonl
"""

import argparse
import json
import random
import unicodedata
from pathlib import Path

QUI = Path(__file__).parent


# --- Verbalizzazione ---------------------------------------------------------

def _senza_accenti(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _elidi_di(sintagma: str) -> str:
    """'fammi un elenco' + 'ordini' -> 'degli ordini'. Articolo determinativo
    contratto con 'di', secondo la fonologia iniziale del sostantivo."""
    p = sintagma.split()[0].lower()
    if p[:1] in "aeiou":
        return f"degli {sintagma}" if p.endswith(("i", "e")) else f"dell'{sintagma}"
    if p.startswith(("gn", "ps", "x", "z")) or (p.startswith("s") and p[1:2] not in "aeiou"):
        return f"degli {sintagma}"
    if p.endswith("e") and not p.endswith("le"):
        return f"delle {sintagma}"
    if p.endswith("i"):
        return f"dei {sintagma}"
    return f"delle {sintagma}" if p.endswith("a") else f"dei {sintagma}"


class Verbalizzatore:
    """Trasforma uno stato in una frase italiana plausibile."""

    def __init__(self, l1: dict, rng: random.Random):
        self.l1 = l1
        self.rng = rng

    def _termine_entita(self, chiave: str, ambiguo: bool = False) -> str:
        e = self.l1["entita"][chiave]
        if ambiguo and e.get("gergo_ambiguo"):
            return self.rng.choice(e["gergo_ambiguo"])
        return self.rng.choice(e["termini"])

    def _termine_attributo(self, campo: str) -> str:
        """Solo forme nominali: usabili dopo 'per' e 'con'."""
        voce = self.l1["attributi"].get(campo)
        if not voce:
            return campo
        return self.rng.choice(voce["nominali"] or [campo])

    def _termine_categoria(self, categoria: str, genere: str) -> str:
        """Accorda l'aggettivo al genere dell'entita; le locuzioni sono invarianti."""
        c = self.l1["categorie"][categoria]
        candidati = list(c["termini_inv"]) + list(c[f"termini_{genere}"])
        return self.rng.choice(candidati) if candidati else categoria

    def frase(self, stato: dict, ambiguo: bool = False) -> str:
        genere = self.l1["entita"][stato["target"]]["genere"]
        usa_di = self.rng.random() < 0.15
        if usa_di:
            v = self.rng.choice(self.l1["verbi_richiesta"]["con_di"])
            entita = self._termine_entita(stato["target"], ambiguo)
            testa = f"{v} {_elidi_di(entita)}"
        else:
            v = self.rng.choice(
                self.l1["verbi_richiesta"]["colloquiale"]
                + self.l1["verbi_richiesta"]["neutro"]
            )
            testa = f"{v} {self._termine_entita(stato['target'], ambiguo)}"
        pezzi = [testa]

        for c in stato["filter"]:
            if c["tipo"] == "categoria":
                pezzi.append(self._termine_categoria(c["categoria"], genere))
            elif c["tipo"] == "temporale":
                pezzi.append(c["espressione"])
            elif c["tipo"] == "confronto":
                gruppo = ("confronto_sopra" if c["verso"] == "sopra"
                          else "confronto_sotto")
                op = self.rng.choice(self.l1["vaghezza"][gruppo])
                attr = self._termine_attributo(c["campo"])
                if "..." in op:                       # circonfisso: "da ... in su"
                    prima, dopo = (p.strip() for p in op.split("..."))
                    pezzi.append(f"con {attr} {prima} {c['valore']} {dopo}")
                else:
                    pezzi.append(f"con {attr} {op} {c['valore']}")
            elif c["tipo"] == "riferimento":
                pezzi.append(f"di {c['valore']}")

        if stato["group_by"]:
            pezzi.append(f"raggruppati per {self._termine_attributo(stato['group_by'][0])}")
        if stato["order"]:
            pezzi.append(f"ordinati per {self._termine_attributo(stato['order'][0]['campo'])}")
        if stato["fields"]:
            nomi = [self._termine_attributo(f) for f in stato["fields"]]
            pezzi.append("con " + ", ".join(nomi))
        if stato["limit"]["origin"] == "user":
            pezzi.insert(2, f"i primi {stato['limit']['valore']}")

        return " ".join(p for p in pezzi if p).strip()

    def delta(self, operazione: dict, genere: str = "m") -> str:
        """Verbalizza un solo turno di raffinamento."""
        op = operazione["op"]
        if op == "add_condition":
            c = operazione["condition"]
            if c["tipo"] == "categoria":
                t = self._termine_categoria(c["categoria"], genere)
                pron = "quelli" if genere == "m" else "quelle"
                return self.rng.choice(
                    [f"solo {t}", f"solo {pron} {t}", f"e {t}", f"filtra {t}", t])
            if c["tipo"] == "temporale":
                return self.rng.choice([c["espressione"], f"solo {c['espressione']}"])
        if op == "add_order":
            a = self._termine_attributo(operazione["campo"])
            return self.rng.choice([f"ordina per {a}", f"per {a}", f"mettili in ordine di {a}"])
        if op == "add_field":
            a = self._termine_attributo(operazione["campo"])
            return self.rng.choice([f"mostrami anche {a}", f"aggiungi {a}", f"e anche {a}"])
        if op == "add_group":
            a = self._termine_attributo(operazione["campo"])
            return self.rng.choice([f"raggruppa per {a}", f"dividili per {a}"])
        if op == "set_limit":
            return f"solo i primi {operazione['valore']}"
        return "?"


# --- Perturbazione (metodo Spider-Syn / Spider-Realistic) --------------------

class Perturbatore:
    def __init__(self, l1: dict, rng: random.Random):
        self.f = l1["fenomeni_linguistici"]
        self.rng = rng

    def applica(self, testo: str) -> tuple[str, list[str]]:
        applicate = []
        if self.rng.random() < 0.18:
            for pieno, breve in self.f["abbreviazioni"].items():
                if pieno in testo:
                    testo = testo.replace(pieno, breve, 1)
                    applicate.append("abbreviazione")
                    break
        if self.rng.random() < 0.12:
            for giusto, sbagliato in self.f["refusi_frequenti"].items():
                if giusto in testo:
                    testo = testo.replace(giusto, sbagliato, 1)
                    applicate.append("refuso")
                    break
        if self.rng.random() < 0.10:
            for it, en in self.f["code_switching"].items():
                if it in testo:
                    testo = testo.replace(it, en, 1)
                    applicate.append("code_switching")
                    break
        if self.rng.random() < 0.15:
            testo = testo.lower()
            applicate.append("minuscole")
        if self.rng.random() < 0.08:
            testo = _senza_accenti(testo)
            applicate.append("senza_accenti")
        return testo, applicate


# --- Generazione degli stati -------------------------------------------------

CATALOGO = {
    "sale.order": {
        "categorie": ["da_fatturare", "da_consegnare", "confermati", "in_bozza"],
        "campi": ["partner_id", "user_id", "amount_total", "date_order", "state"],
        "temporali": ["date_order"],
        "raggruppabili": ["user_id", "partner_id", "state"],
    },
    "account.move.out_invoice": {
        "categorie": ["fatture_scadute", "partite_aperte", "in_bozza"],
        "campi": ["partner_id", "amount_total", "invoice_date", "invoice_date_due", "payment_state"],
        "temporali": ["invoice_date", "invoice_date_due"],
        "raggruppabili": ["partner_id", "payment_state"],
    },
    "res.partner.customer": {
        "categorie": ["attivi"],
        "campi": ["city", "country_id", "phone", "email", "vat"],
        "temporali": [],
        "raggruppabili": ["city", "country_id"],
    },
    "product.template": {
        "categorie": ["sottoscorta", "attivi"],
        "campi": ["categ_id", "qty_available"],
        "temporali": [],
        "raggruppabili": ["categ_id"],
    },
    "crm.lead": {
        "categorie": ["confermati", "attivi"],
        "campi": ["partner_id", "user_id", "expected_revenue", "stage_id", "team_id"],
        "temporali": [],
        "raggruppabili": ["user_id", "stage_id", "team_id"],
    },
    "stock.picking": {
        "categorie": ["da_consegnare", "in_bozza"],
        "campi": ["partner_id", "state"],
        "temporali": [],
        "raggruppabili": ["state"],
    },
}


class Generatore:
    def __init__(self, l1: dict, rng: random.Random):
        self.l1, self.rng = l1, rng
        self.verb = Verbalizzatore(l1, rng)
        self.pert = Perturbatore(l1, rng)

    def _stato(self, target: str, n_cond: int) -> dict:
        spec = CATALOGO[target]
        stato = {"target": target, "filter": [], "fields": [], "group_by": [],
                 "order": [], "limit": {"valore": 80, "origin": "default"},
                 "presentation": "list"}
        # Una condizione per campo e una sola temporale: due vincoli sullo stesso
        # campo produrrebbero uno stato incoerente, respinto dalla validazione di
        # livello 4 — quindi un caso il cui atteso e' sbagliato.
        campi_usati: set[str] = set()
        numerici = [c for c in spec["campi"] if "amount" in c or "qty" in c
                    or "revenue" in c]
        scelte = []
        if spec["categorie"]:
            scelte.append("categoria")
        if spec["temporali"]:
            scelte.append("temporale")
        if numerici:
            scelte.append("confronto")

        for _ in range(n_cond):
            tipo = self.rng.choice(scelte)
            if tipo == "categoria":
                disponibili = [c for c in spec["categorie"]
                               if not (set(self.l1["categorie"][c].get("campi_implicati", []))
                                       & campi_usati)
                               and all(f.get("categoria") != c for f in stato["filter"])]
                if not disponibili:
                    continue
                c = self.rng.choice(disponibili)
                stato["filter"].append({"tipo": "categoria", "categoria": c})
                campi_usati |= set(self.l1["categorie"][c].get("campi_implicati", []))
            elif tipo == "temporale":
                if any(f["tipo"] == "temporale" for f in stato["filter"]):
                    continue
                campo = self.rng.choice(spec["temporali"])
                if campo in campi_usati:
                    continue
                stato["filter"].append({
                    "tipo": "temporale", "campo": campo,
                    "espressione": self.rng.choice(
                        self.l1["temporali"]["correnti"]
                        + self.l1["temporali"]["precedenti"]
                        + self.l1["temporali"]["relativi"]
                        + self.l1["temporali"]["assoluti"]),
                })
                campi_usati.add(campo)
            else:
                liberi = [c for c in numerici if c not in campi_usati]
                if not liberi:
                    continue
                campo = self.rng.choice(liberi)
                stato["filter"].append({
                    "tipo": "confronto", "campo": campo,
                    "verso": self.rng.choice(["sopra", "sotto"]),
                    "valore": self.rng.choice([100, 500, 1000, 5000, 10000]),
                })
                campi_usati.add(campo)
        if self.rng.random() < 0.30 and spec["raggruppabili"]:
            stato["group_by"] = [self.rng.choice(spec["raggruppabili"])]
        if self.rng.random() < 0.35:
            stato["order"] = [{"campo": self.rng.choice(spec["campi"]), "verso": "desc"}]
        if self.rng.random() < 0.30:
            stato["fields"] = self.rng.sample(spec["campi"], min(3, len(spec["campi"])))
        if self.rng.random() < 0.18:
            stato["limit"] = {"valore": self.rng.choice([5, 10, 20]), "origin": "user"}
        return stato

    def _riferimenti(self, stato: dict) -> list[str]:
        rif = [stato["target"]]
        for c in stato["filter"]:
            if c["tipo"] == "categoria":
                rif.append(f"categoria:{c['categoria']}")
            elif "campo" in c:
                rif.append(f"{stato['target']}.{c['campo']}")
        rif += [f"{stato['target']}.{c}" for c in stato["fields"]]
        rif += [f"{stato['target']}.{g}" for g in stato["group_by"]]
        rif += [f"{stato['target']}.{o['campo']}" for o in stato["order"]]
        return sorted(set(rif))

    def caso_apertura(self, idx: int) -> dict:
        target = self.rng.choice(list(CATALOGO))
        stato = self._stato(target, self.rng.choice([0, 1, 1, 2, 2, 3]))
        testo = self.verb.frase(stato)
        testo, fen = self.pert.applica(testo)
        return {
            "id": f"F{idx:05d}", "tipo": "apertura", "esito_atteso": "operations",
            "testo": testo, "stato_partenza": None, "stato_atteso": stato,
            "riferimenti_necessari": self._riferimenti(stato),
            "etichette": {"entita": target, "fenomeni": fen,
                          "difficolta": ["facile", "media", "difficile"][min(2, len(stato["filter"]))]},
        }

    def caso_raffinamento(self, idx: int) -> dict:
        target = self.rng.choice(list(CATALOGO))
        spec = CATALOGO[target]
        base = self._stato(target, self.rng.choice([1, 2]))
        possibili = ["add_order", "add_field"]
        if spec["categorie"]:
            possibili.append("add_condition")
        if spec["raggruppabili"]:
            possibili.append("add_group")
        possibili.append("set_limit")
        op = self.rng.choice(possibili)
        if op == "add_condition":
            operazione = {"op": op, "condition": {
                "tipo": "categoria", "categoria": self.rng.choice(spec["categorie"])}}
        elif op == "set_limit":
            operazione = {"op": op, "valore": self.rng.choice([5, 10, 20])}
        else:
            campo = self.rng.choice(
                spec["raggruppabili"] if op == "add_group" else spec["campi"])
            operazione = {"op": op, "campo": campo}
        testo = self.verb.delta(operazione, self.l1["entita"][target]["genere"])
        testo, fen = self.pert.applica(testo)
        return {
            "id": f"F{idx:05d}", "tipo": "raffinamento", "esito_atteso": "operations",
            "testo": testo, "stato_partenza": base, "operazioni_attese": [operazione],
            "riferimenti_necessari": self._riferimenti(base),
            "etichette": {"entita": target, "fenomeni": fen, "difficolta": "media"},
        }

    def caso_chiarimento(self, idx: int) -> dict:
        """Termini deliberatamente ambigui: l'esito corretto e' una domanda."""
        modo = self.rng.choice(["entita_ambigua", "definizione_mancante", "ruolo_ambiguo"])
        verbo = self.rng.choice(self.l1["verbi_richiesta"]["colloquiale"]
                                + self.l1["verbi_richiesta"]["neutro"])
        if modo == "entita_ambigua":
            gergo = self.rng.choice(["le pratiche aperte", "i lavori in corso",
                                     "le commesse aperte", "i documenti di ieri"])
            testo = f"{verbo} {gergo}"
            motivo = "termine di gergo non mappato: puo' indicare piu' entita"
        elif modo == "definizione_mancante":
            c = self.l1["categorie"]["clienti_importanti"]
            t = self.rng.choice(c["termini_m"] + c["termini_inv"])
            soggetto = self.rng.choice(["i clienti", "gli ordini", "gli articoli"])
            testo = f"{verbo} {soggetto} {t}"
            motivo = "vaghezza qualitativa priva di definizione L2"
        else:
            cognome = self.rng.choice(["Rossi", "Bianchi", "Ferrari", "Conti"])
            testo = self.rng.choice([
                f"{verbo} gli ordini di {cognome}",
                f"{verbo} le fatture di {cognome}",
            ])
            motivo = f"'di {cognome}' ammette lettura come cliente o come venditore"
        testo, fen = self.pert.applica(testo)
        return {
            "id": f"F{idx:05d}", "tipo": "chiarimento", "esito_atteso": "clarification",
            "testo": testo, "stato_partenza": None, "motivo_atteso": motivo,
            "riferimenti_necessari": [],
            "etichette": {"entita": None, "fenomeni": fen, "difficolta": "difficile"},
        }

    def caso_fuori_ambito(self, idx: int) -> dict:
        testo, nota = self.rng.choice([
            ("cambia lo stato di questo ordine a confermato", "modifica_dati"),
            ("mandami questo report per email", "invio_esterno"),
            ("crea un nuovo cliente Mario Bianchi", "creazione_record"),
            ("elimina le fatture in bozza", "cancellazione_record"),
            ("fammi una previsione delle vendite del prossimo trimestre", "previsione"),
            ("conferma tutti gli ordini in bozza", "modifica_dati"),
        ])
        testo, fen = self.pert.applica(testo)
        return {
            "id": f"F{idx:05d}", "tipo": "fuori_ambito", "esito_atteso": "out_of_scope",
            "testo": testo, "stato_partenza": None, "scope_note_atteso": nota,
            "riferimenti_necessari": [],
            "etichette": {"entita": None, "fenomeni": fen, "difficolta": "facile"},
        }

    def caso_incompreso(self, idx: int) -> dict:
        testo = self.rng.choice([
            "ciao come stai", "boh", "quella cosa di ieri",
            "fammi vedere quella roba", "il coso del tizio",
        ])
        return {
            "id": f"F{idx:05d}", "tipo": "incompreso", "esito_atteso": "not_understood",
            "testo": testo, "stato_partenza": None, "riferimenti_necessari": [],
            "etichette": {"entita": None, "fenomeni": [], "difficolta": "facile"},
        }


# --- Composizione secondo il bilanciamento di D46 ---------------------------

QUOTE = [
    ("raffinamento", 0.42),   # D46: >= 40%
    ("chiarimento", 0.11),    # D46: >= 10%
    ("fuori_ambito", 0.06),   # D46: >= 5%
    ("incompreso", 0.04),     # D46: >= 3%
    ("apertura", 0.37),
]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=600)
    p.add_argument("--seme", type=int, default=42)
    p.add_argument("--l1", default=str(QUI / "lessico_l1.json"))
    p.add_argument("--out", default=str(QUI / "corpus_fondativo.jsonl"))
    args = p.parse_args()

    rng = random.Random(args.seme)
    l1 = json.loads(Path(args.l1).read_text(encoding="utf-8"))
    g = Generatore(l1, rng)

    piano = []
    for tipo, quota in QUOTE:
        piano += [tipo] * round(args.n * quota)
    rng.shuffle(piano)

    metodo = {
        "apertura": g.caso_apertura, "raffinamento": g.caso_raffinamento,
        "chiarimento": g.caso_chiarimento, "fuori_ambito": g.caso_fuori_ambito,
        "incompreso": g.caso_incompreso,
    }
    casi = [metodo[t](i + 1) for i, t in enumerate(piano)]

    with Path(args.out).open("w", encoding="utf-8") as f:
        for c in casi:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    conteggi: dict = {}
    entita: dict = {}
    fenomeni: dict = {}
    for c in casi:
        conteggi[c["tipo"]] = conteggi.get(c["tipo"], 0) + 1
        e = c["etichette"]["entita"]
        if e:
            entita[e] = entita.get(e, 0) + 1
        for ph in c["etichette"]["fenomeni"]:
            fenomeni[ph] = fenomeni.get(ph, 0) + 1

    print(f"casi generati: {len(casi)}  seme: {args.seme}\n")
    print("per tipo")
    for k, v in sorted(conteggi.items(), key=lambda x: -x[1]):
        print(f"  {k:15} {v:5}  {v / len(casi):6.1%}")
    print("\nper entita")
    for k, v in sorted(entita.items(), key=lambda x: -x[1]):
        print(f"  {k:30} {v:5}  {v / len(casi):6.1%}")
    print("\nfenomeni linguistici applicati")
    for k, v in sorted(fenomeni.items(), key=lambda x: -x[1]):
        print(f"  {k:15} {v:5}")
    print(f"\nScritto in {args.out}")


if __name__ == "__main__":
    main()
