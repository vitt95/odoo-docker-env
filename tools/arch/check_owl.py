"""Il quinto controllo: cio' che il lato client dichiara e nessuno legge.

Due regole, la stessa famiglia di guasto — **un nome che sembra collegato e non lo e'**,
in un punto del prodotto dove non esiste nessuna prova che se ne accorga.

## Regola 1 — un componente OWL dichiarato e non importato

### Perché esiste

Il 2 agosto 2026 una riga aggiunta a mano ha messo `AidaRecords` fra i
`static components` di `AidaThread` **senza importarlo**. Il modulo fallisce alla
valutazione, `AidaThread` non si definisce, e il filo dei messaggi sparisce — con lui
le opzioni di disambiguazione, che è come il difetto si è manifestato.

Nessuno se n'è accorto per il tempo di due distribuzioni. Non perché mancasse una
prova: perché **non esiste nessuna prova del lato client** in questo progetto, e i 147
test Odoo erano verdi mentre la chat non si apriva. Un controllo statico non sostituisce
le prove che mancano, ma questa classe di errore — un nome usato e mai importato — è
esattamente ciò che uno statico prende senza far girare niente.

## Cosa guarda, e cosa non guarda

Guarda i nomi dentro `static components = { ... }` e verifica che ognuno compaia in un
`import` dello stesso file. Non è un analizzatore JavaScript e non pretende di esserlo:
prende il caso in cui il nome non c'è proprio, che è il caso capitato e il più facile da
introdurre modificando un file a colpi di sostituzione.

Le abbreviazioni di oggetto (`{ AidaRecords }`) e le rinomine (`{ X: Y }`) si
raccolgono entrambe: nella seconda il nome che deve esistere è il valore, non la chiave.

## Regola 2 — una chiave di contesto che Odoo non conosce

### Perché esiste

Il 3 agosto 2026, sul campo: *«i primi 5 lead ordinati per data di creazione»*. Il piano
diceva `limit 5`, il server leggeva cinque record, e la tabella ne mostrava
**trentanove**. Il limite viaggiava verso la vista come `list_view_limit` nel contesto, e
quella chiave **non esiste in Odoo 18**: zero occorrenze in tutto `web/static/src`. Non
la leggeva nessuno, e la lista mostrava le sue righe predefinite.

È il reperto R2 dell'audit per la seconda volta nello stesso componente — *una chiave
passata a chi non la legge* — e la ragione per cui torna è sempre quella: dal lato client
non c'è nessuna prova. Nel frattempo uno statico questa classe la prende senza far girare
niente, perché la domanda è verificabile leggendo: **questa parola, Odoo la conosce?**

### Cosa guarda, e cosa non guarda

Le chiavi dentro un blocco `context: { ... }` dei nostri componenti, confrontate con
tutto il sorgente JavaScript di `web/static/src`. Una chiave che lì non compare mai non
la legge nessuno.

Non dice il contrario: una chiave che *esiste* può essere passata nel posto sbagliato, e
questo controllo non se ne accorge. Prende il caso in cui la parola non esiste proprio,
che è quello capitato e quello che nessuno rilegge.

Se un giorno servisse una chiave nostra — letta dal nostro Python e non da Odoo — va
messa in `NOSTRE` qui sotto, **con il motivo**. Un elenco di eccezioni senza motivi
diventa il posto dove si nasconde il prossimo difetto.
"""

from __future__ import annotations

import re
from pathlib import Path

from .report import CheckResult, Violation
from .spec import ADDONS_DIR, REPO_ROOT

#: `static components = { ... }` fino alla graffa di chiusura. Non annidiamo: un
#: blocco `components` con oggetti dentro non esiste in nessun OWL scritto a mano.
_COMPONENTS = re.compile(r"static\s+components\s*=\s*\{([^}]*)\}", re.S)

#: Un `import` qualunque, di cui interessa solo la lista dei nomi legati.
_IMPORT = re.compile(r"^\s*import\s+(.+?)\s+from\s+['\"]", re.M)

#: `context: { ... }` fino alla graffa di chiusura, senza annidare: i nostri contesti
#: sono piatti, e uno che non lo fosse sfuggirebbe invece di dare un falso allarme.
_CONTEXT = re.compile(r"context:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.S)

#: Una chiave di oggetto: `nome:` a inizio voce. Le voci sparse (`...(x ? {a: 1} : {})`)
#: si sciolgono da sole, perche' la chiave resta scritta com'e'.
_CHIAVE = re.compile(r"([A-Za-z_$][\w$]*)\s*:")

#: I commenti, che vanno via **prima** di cercare le chiavi. Senza, una riga come
#: *«D2: da qui non si scrive»* diventa una chiave di contesto chiamata `D2`, e un
#: controllo che segnala le proprie note e' un controllo che si impara a ignorare.
_COMMENTO = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)

#: Il sorgente di Odoo dove una chiave di contesto deve comparire per essere letta.
_CORE_JS = "core/addons/web/static/src"

#: Chiavi nostre, che Odoo non conosce di proposito. Vuoto, e va tenuto vuoto: ogni
#: voce qui e' una cosa che il lato client si aspetta e che nessuno verifica.
NOSTRE: frozenset[str] = frozenset()


def _declared(block: str) -> list[str]:
    """I nomi che il blocco `components` pretende esistano in questo file."""
    nomi = []
    for voce in block.split(","):
        voce = voce.strip()
        if not voce or voce.startswith("..."):
            continue
        # `{ X: Y }` lega Y; `{ X }` lega X.
        nome = voce.split(":")[-1].strip()
        if re.fullmatch(r"[A-Za-z_$][\w$]*", nome):
            nomi.append(nome)
    return nomi


def _imported(source: str) -> set[str]:
    nomi: set[str] = set()
    for clausola in _IMPORT.findall(source):
        for pezzo in re.split(r"[{},]", clausola):
            pezzo = pezzo.strip()
            if not pezzo or pezzo == "*":
                continue
            # `import X as Y` e `{ X as Y }` legano Y.
            nome = re.split(r"\s+as\s+", pezzo)[-1].strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", nome):
                nomi.add(nome)
    return nomi


def _core_source() -> str:
    """Tutto il JavaScript di Odoo in un testo solo, letto una volta.

    Sette megabyte, e si leggono in un secondo: il controllo gira prima di ogni suite e
    prima di ogni misura, e un secondo li' costa meno di un pomeriggio a cercare perche'
    la tabella mostra trentanove righe invece di cinque.
    """
    radice = REPO_ROOT / _CORE_JS
    if not radice.is_dir():
        return ""
    return "\n".join(
        percorso.read_text(encoding="utf-8", errors="ignore")
        for percorso in sorted(radice.rglob("*.js")))


def run() -> CheckResult:
    result = CheckResult(name="OWL components", unit="javascript files")
    sorgente_odoo = _core_source()

    for path in sorted(ADDONS_DIR.glob("nli_*/static/src/**/*.js")):
        result.inspected += 1
        source = path.read_text(encoding="utf-8")
        importati = _imported(source)
        # Una classe definita nello stesso file va bene quanto una importata.
        definiti = set(re.findall(r"^\s*(?:export\s+)?class\s+([\w$]+)", source, re.M))
        disponibili = importati | definiti

        for blocco in _COMPONENTS.findall(source):
            for nome in _declared(blocco):
                if nome in disponibili:
                    continue
                relativo = path.relative_to(REPO_ROOT)
                riga = source[:source.index(nome)].count("\n") + 1
                result.add(Violation(
                    rule="component declared but never imported",
                    location=f"{relativo}:{riga}",
                    detail=(
                        f"'{nome}' is listed in `static components` but no import or "
                        f"class in this file binds it. The module throws when it is "
                        f"evaluated, the component never registers, and everything "
                        f"the template draws disappears without a server error"
                    ),
                    protects="client",
                ))

        if not sorgente_odoo:
            # Senza il sorgente di Odoo la seconda regola non puo' dire niente, e
            # tacere e' l'unica risposta onesta: un controllo che passa perche' non ha
            # guardato e' peggio di un controllo che manca.
            continue

        for blocco in _CONTEXT.findall(_COMMENTO.sub("", source)):
            for chiave in dict.fromkeys(_CHIAVE.findall(blocco)):
                if chiave in NOSTRE or re.search(rf"\b{re.escape(chiave)}\b",
                                                 sorgente_odoo):
                    continue
                relativo = path.relative_to(REPO_ROOT)
                posizione = source.find(f"{chiave}:")
                riga = source[:max(posizione, 0)].count("\n") + 1
                result.add(Violation(
                    rule="context key Odoo does not know",
                    location=f"{relativo}:{riga}",
                    detail=(
                        f"'{chiave}' is passed in a view context but appears nowhere "
                        f"in {_CORE_JS}. Nothing reads it, so the view silently keeps "
                        f"its own default — which is how 'the first 5' showed 39 rows. "
                        f"Find the key Odoo really reads, or declare it in NOSTRE with "
                        f"the reason"
                    ),
                    protects="client",
                ))

    return result
