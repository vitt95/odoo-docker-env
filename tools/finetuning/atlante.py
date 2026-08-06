"""L'atlante: tutto quello che AIDA può nominare in un'installazione Odoo Community.

Si esegue nella shell di Odoo, su una banca dati con tutte e trentacinque le
applicazioni installate e l'italiano caricato:

    ./manage.sh atlante atlante            # etichette italiane
    ./manage.sh atlante atlante en_US      # le stesse entita', etichette inglesi

## La seconda raccolta, in inglese

`ai/18` §5bis chiede che il 15% degli esempi di addestramento porti un catalogo con le
etichette **in inglese** e la domanda in italiano: un'installazione Odoo puo' girare in
inglese e succede spessissimo anche in Italia. E' il caso piu' istruttivo che abbiamo —
se il modello risolve *«mostrami gli ordini di questo mese»* su un catalogo che dice
`Order Date`, ha imparato ad agganciare **significati**, non parole.

Quel documento prevedeva **una seconda banca dati senza l'italiano caricato**. Non
serve: le etichette inglesi sono gia' in questa, perche' l'inglese e' la lingua
*sorgente* di Odoo e l'italiano e' una traduzione che ci sta sopra. Basta leggere con
un'altra lingua nel contesto — `ATLANTE_LANG` — e le due versioni sono allineate per
riferimento **per costruzione**, invece che da un passo di allineamento che potrebbe
sbagliare. Una banca dati in meno da costruire e da tenere allineata.

## Perché esiste

Il dataset di addestramento deve insegnare al modello a **leggere il catalogo**, non a
ricordarsi otto entità. Per farlo servono catalogo e vocabolario di tutte le
applicazioni — e non li inventiamo noi: **ce li ha già Odoo**, nelle etichette dei
campi, nei valori degli elenchi e nelle relazioni, tradotti in italiano dai suoi stessi
file di lingua. È **D126** (le parole si raccolgono dall'installazione invece di
generarle) applicato a tutto il prodotto invece che a otto entità.

E si raccoglie con **la nostra introspezione**, non leggendo il sorgente: i tipi del
contratto, il filtro dei permessi e le regole di esposizione sono già scritti una volta
sola in `nli_semantics`, e una seconda copia scritta per il dataset comincerebbe a
divergere il giorno dopo — insegnando al modello un mondo che il prodotto non ha.

## Cosa raccoglie, per ogni entità

Il riferimento, i termini con cui si può nominare, l'applicazione che la porta, e per
ogni attributo nominabile il riferimento, i termini, il tipo del contratto e — se è un
enumerato — i valori ammessi con le loro parole.

**Tutti** gli attributi, non i sessanta del tetto di **D31**: il budget si applica quando
si costruisce il catalogo di una domanda, e il generatore lo farà, variandolo. Qui
serve l'insieme completo da cui pescare.

## Cosa non raccoglie

Nessun dato: né record, né valori di campo, né conteggi. L'atlante è **schema**, e §3.3
(A6) chiede esattamente questo — il catalogo mostra cosa esiste come struttura, mai il
contenuto di una riga.
"""

import json
import os
import sys

from odoo.addons.nli_semantics.introspection import l0

#: Modelli che nessuno nomina in una domanda: tecnici, di servizio, o procedure guidate.
#: Il filtro è largo di proposito — quello fine lo fanno le regole di esposizione, e
#: quello che passa di qui e non ha attributi nominabili cade da solo più avanti.
PREFISSI_ESCLUSI = (
    "ir.", "bus.", "base.", "res.config", "report.", "web_editor.", "web_tour.",
    "mail.message", "mail.notification", "mail.followers", "mail.tracking",
    "format.address", "publisher_warranty", "iap.", "onboarding.",
)

#: Suffissi delle procedure guidate: esistono per un modulo, non per una domanda.
SUFFISSI_ESCLUSI = (".wizard", ".mixin", ".template.mixin", ".report")

#: Sotto questa soglia un'entità non regge nemmeno una domanda: un attributo solo non
#: fa un catalogo, e un caso costruito lì insegnerebbe una forma che non esiste.
ATTRIBUTI_MINIMI = 4


def _candidati(env):
    """I modelli che vale la pena guardare, prima che le regole vere decidano."""
    nomi = []
    for nome in sorted(env.registry):
        if nome.startswith(PREFISSI_ESCLUSI) or nome.endswith(SUFFISSI_ESCLUSI):
            continue
        modello = env[nome]
        if modello._abstract or modello._transient or not modello._auto:
            continue
        nomi.append(nome)
    return nomi


def _applicazioni(env, nome_modello):
    """I moduli che definiscono il modello: servono a tenere fuori dall'addestramento
    intere applicazioni, che è l'unico insieme di prova che dimostri qualcosa."""
    riga = env["ir.model"].search([("model", "=", nome_modello)], limit=1)
    return sorted((riga.modules or "").replace(" ", "").split(",")) if riga else []


def _termini(dizionario, riferimento):
    voce = dizionario.resolved.get(("T1", riferimento))
    return list(voce.get("terms") or ()) if voce else []


def _valori(dizionario, riferimento):
    """I valori di un enumerato (T2), con le parole che li nominano."""
    trovati = []
    for voce in dizionario.raw:
        if voce.get("type") != "T2" or voce.get("ref") != riferimento:
            continue
        trovati.append({"valore": voce.get("value"),
                        "termini": list(voce.get("terms") or ())})
    return trovati


def raccogli(env, massimo=None):
    from odoo.addons.nli_semantics.introspection import runtime

    atlante = {"entita": {}, "saltate": []}
    candidati = _candidati(env)
    if massimo:
        candidati = candidati[:massimo]

    for indice, nome in enumerate(candidati, start=1):
        try:
            # Una entità per volta: la semantica di mille modelli in un colpo solo
            # sarebbe enorme e non servirebbe a niente — ogni catalogo è di una
            # entità sola, e così un modello che esplode non porta giù gli altri.
            semantica = runtime.semantics(env, (nome,))
        except Exception as errore:  # noqa: BLE001
            atlante["saltate"].append({"modello": nome, "perche": repr(errore)})
            continue

        riferimento = l0.reference_of_model(nome)
        attributi = []
        for ref, legame in semantica.bindings.items():
            if ref == riferimento or legame.type == "entity":
                continue
            termini = _termini(semantica.dictionary, ref)
            if not termini:
                continue
            voce = {"ref": ref, "tipo": legame.type, "campo": legame.field,
                    "termini": termini}
            if legame.type == "enum":
                voce["valori"] = _valori(semantica.dictionary, ref)
            attributi.append(voce)

        if len(attributi) < ATTRIBUTI_MINIMI:
            atlante["saltate"].append(
                {"modello": nome, "perche": f"{len(attributi)} attributi nominabili"})
            continue

        atlante["entita"][riferimento] = {
            "modello": nome,
            "termini": _termini(semantica.dictionary, riferimento),
            "applicazioni": _applicazioni(env, nome),
            "attributi": attributi,
        }
        print(f"  {indice:4}/{len(candidati)}  {nome:<42} "
              f"{len(attributi):3} attributi", file=sys.stderr)

    return atlante


def main(env):
    # La lingua con cui si legge il catalogo. Assente, si legge con quella della
    # shell — l'italiano, che è la raccolta normale. `en_US` dà le stesse entità con
    # le etichette sorgente di Odoo, allineate per riferimento **per costruzione**:
    # è lo stesso `ref` a portare due nomi, non due raccolte da far combaciare.
    lingua = os.environ.get("ATLANTE_LANG") or None
    if lingua:
        env = env(context=dict(env.context, lang=lingua))
        print(f"  lingua            : {lingua}", file=sys.stderr)

    atlante = raccogli(env)
    atlante["lingua"] = lingua or env.context.get("lang") or "it_IT"
    entita = atlante["entita"]
    tipi = {}
    for voce in entita.values():
        for attributo in voce["attributi"]:
            tipi[attributo["tipo"]] = tipi.get(attributo["tipo"], 0) + 1
    print(f"\n  entita' raccolte : {len(entita)}", file=sys.stderr)
    print(f"  attributi        : {sum(tipi.values())}", file=sys.stderr)
    print(f"  per tipo         : {tipi}", file=sys.stderr)
    print(f"  saltate          : {len(atlante['saltate'])}", file=sys.stderr)
    # Il documento si scrive su un file dentro il contenitore e `manage.sh` lo
    # riporta fuori: l'uscita normale della shell di Odoo porta anche i suoi avvisi,
    # e un JSON con dentro una riga di avviso non è un JSON.
    destinazione = os.environ.get("ATLANTE_OUT", "/var/lib/odoo/atlante.json")
    with open(destinazione, "w", encoding="utf-8") as scrittura:
        json.dump(atlante, scrittura, ensure_ascii=False, indent=1)
    print(f"  scritto           : {destinazione}", file=sys.stderr)
    env.cr.rollback()


main(env)  # noqa: F821 — la shell di Odoo lo mette lei
