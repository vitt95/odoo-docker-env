"""Il pannello di AIDA, guardato davvero: tre temi, quattro gesti, zero errori.

## Perche' esiste

`tools/arch/check_owl.py` lo dice da quando quel controllo e' nato: **non esiste
nessuna prova del lato client in questo progetto**, e i test Odoo sono verdi mentre la
chat non si apre. Il 5 agosto 2026 e' successo di nuovo, cinque volte in un
pomeriggio, sotto 256 prove verdi:

* uno `unquote` mancante fermava la compilazione di **tutto** `web.assets_backend`;
* due nomi di variabile CSS plausibili e inesistenti mandavano AIDA sui valori cablati;
* il testo «Sto pensando…» si leggeva «pensando…», perche' un gradiente ritagliato
  fuori intervallo non sbiadisce le lettere: **le cancella**;
* il pulsante nella barra era grigio scuro su viola;
* la scorciatoia non chiudeva il pannello, perche' il fuoco e' nella casella.

Nessuno di questi rompe una prova Python. Tutti si vedono in due secondi guardando.

Questo copione non e' una suite: e' **il guardare, reso ripetibile**. Non sostituisce
i `tour` di Odoo che un giorno andranno scritti; li anticipa nella sola cosa che
sanno fare gia' oggi, cioe' accorgersi che qualcosa non si disegna.

## Cosa fa

1. Entra con l'utente indicato, apre una vista lista vera e apre il pannello.
2. Legge i token risolti nei **tre temi**. Premium si simula iniettando i `--pui-*`
   della tavolozza: e' esattamente cio' che fa il pacchetto Premium, e prova il primo
   gradino della catena senza pretendere che il tema sia installato.
3. Prova i gesti che si rompono in silenzio: trascinamento, confini, cronologia,
   scorciatoia, bozza che sopravvive alla chiusura.
4. Raccoglie **ogni** errore JavaScript della pagina e fallisce se ce n'e' uno.

## Come si usa

    python3 tools/ui/verify_panel.py --db nli_test --password <password>

Esce con 0 se tutto passa, 1 al primo problema. Gli screenshot finiscono in
`--out` (predefinito: una cartella temporanea), uno per tema.

Richiede `playwright` e il suo Chromium:

    pip install playwright && playwright install chromium
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - dipende dall'ambiente
    print("playwright non installato: pip install playwright && playwright install chromium")
    raise SystemExit(2)


#: La tavolozza Premium, chiara e scura, come `ui_brand_tokens` la emette.
#: Iniettarla prova il primo gradino della catena dei token senza installare il tema.
PREMIUM = {
    "chiaro": """:root{
        --pui-color-bg:#f7f8fa;--pui-color-surface:#ffffff;
        --pui-color-surface-secondary:#ffffff;--pui-color-surface-sunken:#eef0f4;
        --pui-color-hover:#eef0f4;--pui-color-selected:#e9f2ff;
        --pui-color-border-subtle:#eef0f4;--pui-color-border:#e3e6ec;
        --pui-color-border-strong:#cdd2db;--pui-color-heading:#172b4d;
        --pui-color-text:#2c3e5d;--pui-color-secondary:#44546f;--pui-color-muted:#626f86;
        --pui-color-accent:#0c66e4;--pui-accent-rgb:12,102,228;
    }""",
    "scuro": """:root{
        --pui-color-bg:#1d2125;--pui-color-surface:#22272b;
        --pui-color-surface-secondary:#282e33;--pui-color-surface-sunken:#161a1d;
        --pui-color-hover:#282e33;--pui-color-selected:#09326c;
        --pui-color-border-subtle:#2c333a;--pui-color-border:#38414a;
        --pui-color-border-strong:#5a6772;--pui-color-heading:#dee4ea;
        --pui-color-text:#c3ccd6;--pui-color-secondary:#9fadbc;--pui-color-muted:#8c9bab;
        --pui-color-accent:#579dff;--pui-accent-rgb:87,157,255;
    }""",
}

#: Una vista lista che esiste in qualunque installazione: il pannello va guardato
#: **accanto a del contenuto vero**, perche' meta' del suo senso e' restringerlo.
VISTA = "/odoo/action-base.action_partner_form"

#: I token che devono risolvere a qualcosa. Se uno di questi torna vuoto, la catena si
#: e' rotta da qualche parte e AIDA sta disegnando con i valori di riserva.
TOKEN = ("--aida-bg", "--aida-surface", "--aida-text", "--aida-heading",
         "--aida-accent", "--aida-border", "--aida-muted")


class Esito:
    """Raccoglie i problemi invece di fermarsi al primo: una corsa, tutta la lista."""

    def __init__(self):
        self.problemi: list[str] = []

    def esigi(self, condizione, messaggio: str):
        if condizione:
            print(f"  ok   {messaggio}")
        else:
            print(f"  NO   {messaggio}")
            self.problemi.append(messaggio)


def entra(ctx, base: str, db: str, login: str, password: str):
    page = ctx.new_page()
    errori: list[str] = []
    page.on("pageerror", lambda e: errori.append(str(e)[:200]))
    page.on("console", lambda m: errori.append(f"console.error: {m.text[:200]}")
            if m.type == "error" else None)
    page.goto(f"{base}/web/login?db={db}", wait_until="domcontentloaded")
    page.fill("input[name=login]", login)
    page.fill("input[name=password]", password)
    page.click("button[type=submit]")
    # **Non `networkidle`**: il bus tiene una connessione aperta per sempre, quindi
    # quello stato non arriva mai. Si aspetta l'elemento, che e' cio' che interessa.
    page.wait_for_selector(".o_web_client", timeout=60_000)
    return page, errori


def apri_pannello(page):
    aperto = page.evaluate("odoo.__WOWL_DEBUG__.root.env.services.aida.ui.open")
    if not aperto:
        page.locator(".o_aida_launch_btn").first.click()
        page.wait_for_timeout(1200)
    page.wait_for_timeout(500)


def leggi_token(page) -> dict:
    return page.evaluate("""(nomi) => {
        const el = document.querySelector('.o_aida_panel');
        if (!el) return null;
        const s = getComputedStyle(el);
        const out = {};
        for (const n of nomi) out[n] = s.getPropertyValue(n).trim();
        return out;
    }""", list(TOKEN))


def prova_tema(b, base, db, login, password, nome, css, out: Path, esito: Esito):
    print(f"\n[{nome}]")
    ctx = b.new_context(viewport={"width": 1600, "height": 1000})
    page, errori = entra(ctx, base, db, login, password)
    page.goto(f"{base}{VISTA}", wait_until="domcontentloaded")
    page.wait_for_selector(".o_web_client", timeout=60_000)
    page.wait_for_timeout(3500)
    if css:
        page.add_style_tag(content=css)
        page.wait_for_timeout(400)
    apri_pannello(page)

    esito.esigi(page.locator(".o_aida_panel").count() == 1, f"{nome}: il pannello c'e'")
    token = leggi_token(page)
    esito.esigi(token is not None, f"{nome}: i token si leggono")
    for chiave, valore in (token or {}).items():
        esito.esigi(bool(valore), f"{nome}: {chiave} risolve ({valore or 'VUOTO'})")

    larghezza = page.evaluate(
        "Math.round(document.querySelector('.o_aida_panel').getBoundingClientRect().width)")
    rientro = page.evaluate(
        "getComputedStyle(document.querySelector('.o_action_manager')).paddingRight")
    esito.esigi(rientro == f"{larghezza}px",
                f"{nome}: il contenuto rientra esattamente quanto il pannello "
                f"({rientro} = {larghezza}px)")

    # Il pannello comincia esattamente dove finisce la barra: né sotto, né sopra.
    misure = page.evaluate("""(() => {
        const barra = document.querySelector('.o_navbar').getBoundingClientRect();
        const pan = document.querySelector('.o_aida_panel').getBoundingClientRect();
        return { barraBasso: Math.round(barra.bottom), pannelloAlto: Math.round(pan.top) };
    })()""")
    esito.esigi(misure["barraBasso"] == misure["pannelloAlto"],
                f"{nome}: il pannello comincia dove finisce la barra "
                f"({misure['pannelloAlto']} = {misure['barraBasso']})")

    page.screenshot(path=str(out / f"pannello_{nome}.png"))
    esito.esigi(not errori, f"{nome}: nessun errore JavaScript"
                            + (f" — {errori[:2]}" if errori else ""))
    ctx.close()


def prova_gesti(b, base, db, login, password, out: Path, esito: Esito):
    print("\n[gesti]")
    ctx = b.new_context(viewport={"width": 1600, "height": 1000})
    page, errori = entra(ctx, base, db, login, password)
    page.goto(f"{base}{VISTA}", wait_until="domcontentloaded")
    page.wait_for_selector(".o_web_client", timeout=60_000)
    page.wait_for_timeout(3500)
    apri_pannello(page)

    def larghezza():
        return page.evaluate(
            "Math.round(document.querySelector('.o_aida_panel').getBoundingClientRect().width)")

    def trascina(verso_x: int):
        box = page.locator(".o_aida_resizer").bounding_box()
        page.mouse.move(box["x"] + 3, 500)
        page.mouse.down()
        passo = 40 if verso_x > box["x"] else -40
        for x in range(int(box["x"]), verso_x, passo):
            page.mouse.move(x, 500)
            page.wait_for_timeout(12)
        page.mouse.up()
        page.wait_for_timeout(400)

    # **La barra in alto non si muove.** Il primo difetto visivo segnalato dopo la
    # consegna: il rientro stava sul `body`, che contiene anche la barra, e aprire
    # AIDA faceva scivolare a sinistra il menu applicazioni e il systray. La barra e'
    # il riferimento con cui si ritrova tutto il resto: deve restare ferma.
    def barra():
        return page.evaluate("""(() => {
            const b = document.querySelector('.o_navbar').getBoundingClientRect();
            const s = document.querySelector('.o_menu_systray').getBoundingClientRect();
            return { larghezza: Math.round(b.width), systrayDestra: Math.round(s.right) };
        })()""")

    prima = barra()
    page.evaluate("odoo.__WOWL_DEBUG__.root.env.services.aida.close()")
    page.wait_for_timeout(600)
    chiusa = barra()
    apri_pannello(page)
    dopo = barra()
    esito.esigi(prima == chiusa == dopo,
                f"la barra non si muove aprendo o chiudendo "
                f"(aperta {prima}, chiusa {chiusa}, riaperta {dopo})")

    trascina(60)
    esito.esigi(larghezza() == 800, f"il tetto e' meta' finestra ({larghezza()} su 1600)")
    esito.esigi(barra() == prima,
                f"la barra non si muove nemmeno trascinando ({barra()})")
    trascina(1590)
    esito.esigi(larghezza() == 360, f"il pavimento e' 360 ({larghezza()})")

    salvata = page.evaluate("localStorage.getItem('aida_panel_width')")
    esito.esigi(salvata == "360", f"la larghezza si ricorda ({salvata})")

    page.locator(".o_aida_head .o_aida_icon").first.click()
    page.wait_for_timeout(700)
    esito.esigi(page.locator(".o_aida_history").count() == 1, "la cronologia si apre")
    page.screenshot(path=str(out / "cronologia.png"))
    page.locator(".o_aida_history_veil").click()
    page.wait_for_timeout(400)
    esito.esigi(page.locator(".o_aida_history").count() == 0, "e si chiude dal velo")

    # La bozza deve sopravvivere alla chiusura: vive nello store, non nella casella.
    page.locator(".o_aida_input").fill("le fatture di marzo")
    page.wait_for_timeout(200)
    aperto = lambda: page.evaluate("odoo.__WOWL_DEBUG__.root.env.services.aida.ui.open")
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    esito.esigi(not aperto(), "Escape chiude")
    page.locator(".o_aida_launch_btn").first.click()
    page.wait_for_timeout(900)
    esito.esigi(page.locator(".o_aida_input").input_value() == "le fatture di marzo",
                "la bozza sopravvive alla chiusura")

    # La scorciatoia deve funzionare **anche mentre si scrive**: e' la via d'uscita.
    scorciatoia = "Control+Shift+A" if page.evaluate(
        "/Mac/i.test(navigator.userAgentData?.platform || navigator.platform)") \
        else "Alt+Shift+A"
    page.locator(".o_aida_input").focus()
    page.keyboard.press(scorciatoia)
    page.wait_for_timeout(500)
    esito.esigi(not aperto(), f"{scorciatoia} chiude anche col fuoco nella casella")

    esito.esigi(not errori, "gesti: nessun errore JavaScript"
                            + (f" — {errori[:2]}" if errori else ""))
    ctx.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base", default="http://localhost:8069")
    parser.add_argument("--db", required=True)
    parser.add_argument("--login", default="admin")
    parser.add_argument("--password", required=True)
    parser.add_argument("--out", default=None,
                        help="dove finiscono gli screenshot (default: cartella temporanea)")
    args = parser.parse_args(argv)

    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="aida-ui-"))
    out.mkdir(parents=True, exist_ok=True)
    esito = Esito()

    with sync_playwright() as p:
        b = p.chromium.launch()
        prova_tema(b, args.base, args.db, args.login, args.password,
                   "classic", None, out, esito)
        prova_tema(b, args.base, args.db, args.login, args.password,
                   "premium-chiaro", PREMIUM["chiaro"], out, esito)
        prova_tema(b, args.base, args.db, args.login, args.password,
                   "premium-scuro", PREMIUM["scuro"], out, esito)
        prova_gesti(b, args.base, args.db, args.login, args.password, out, esito)
        b.close()

    print(f"\nScreenshot in {out}")
    if esito.problemi:
        print(f"\n{len(esito.problemi)} problemi:")
        for problema in esito.problemi:
            print(f"  - {problema}")
        return 1
    print("\nTutto a posto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
