#!/usr/bin/env python3
"""
Estrazione del lessico L0 dai sorgenti Odoo.

Produce il vocabolario ufficiale — entità, attributi, valori enumerati, filtri
nominati — nella lingua dell'installazione, a partire dai file di traduzione e
dalle viste di ricerca.

E' la fonte deterministica del corpus fondativo: non richiede clienti, non
richiede giudizio, ed e' rigenerabile in modo identico a ogni aggiornamento
(cfr. 06-modello-semantico.md §2.4).

Uso:
    python3 estrai_lessico.py --core ../../core --lingua it --out lessico_l0.json
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# --- Riferimenti nei file .po che ci interessano -----------------------------
# Odoo marca ogni traduzione con il tipo di elemento a cui si riferisce.
RIF_CAMPO = re.compile(
    r"^#:\s+model:ir\.model\.fields,field_description:"
    r"(?P<modulo>[\w.]+)\.field_(?P<modello>\w+)__(?P<campo>\w+)"
)
RIF_MODELLO = re.compile(r"^#:\s+model:ir\.model,name:(?P<modulo>[\w.]+)\.model_(?P<modello>\w+)")
RIF_SELEZIONE = re.compile(
    r"^#:\s+model:ir\.model\.fields\.selection,name:"
    r"(?P<modulo>[\w.]+)\.selection__(?P<modello>\w+)__(?P<campo>\w+)__(?P<valore>\w+)"
)

MSGID = re.compile(r'^msgid\s+"(?P<t>.*)"')
MSGSTR = re.compile(r'^msgstr\s+"(?P<t>.*)"')
CONTINUA = re.compile(r'^"(?P<t>.*)"')

# Filtri nominati nelle viste di ricerca: sono le categorie gia' curate
# dai progettisti dei moduli (cfr. D35).
FILTRO = re.compile(r'<filter\b[^>]*?\bname="(?P<nome>[^"]+)"[^>]*?\bstring="(?P<etichetta>[^"]+)"')
FILTRO_INV = re.compile(r'<filter\b[^>]*?\bstring="(?P<etichetta>[^"]+)"[^>]*?\bname="(?P<nome>[^"]+)"')

# Campi che non entrano mai nel catalogo (cfr. 06 §5.3, regole 2 e 3).
CAMPI_SISTEMA = {
    "id", "create_uid", "create_date", "write_uid", "write_date",
    "display_name", "__last_update",
}
PREFISSI_TECNICI = ("message_", "activity_", "rating_", "website_message_")


def _blocchi_po(percorso: Path):
    """Genera (righe_riferimento, msgid, msgstr) per ogni voce del file .po."""
    rif, msgid, msgstr, stato = [], None, None, None
    with percorso.open(encoding="utf-8", errors="replace") as f:
        for riga in f:
            riga = riga.rstrip("\n")
            if riga.startswith("#:"):
                if stato == "str" and msgid is not None:
                    yield rif, msgid, msgstr
                    rif, msgid, msgstr, stato = [], None, None, None
                rif.append(riga)
                continue
            m = MSGID.match(riga)
            if m:
                msgid, stato = m.group("t"), "id"
                continue
            m = MSGSTR.match(riga)
            if m:
                msgstr, stato = m.group("t"), "str"
                continue
            m = CONTINUA.match(riga)
            if m and stato:
                if stato == "id":
                    msgid += m.group("t")
                else:
                    msgstr += m.group("t")
                continue
            if not riga.strip():
                if stato == "str" and msgid is not None:
                    yield rif, msgid, msgstr
                rif, msgid, msgstr, stato = [], None, None, None
    if stato == "str" and msgid is not None:
        yield rif, msgid, msgstr


def _esposto(campo: str) -> bool:
    """Applica le esclusioni deterministiche di 06 §5.3 (regole 2 e 3)."""
    if campo in CAMPI_SISTEMA:
        return False
    return not campo.startswith(PREFISSI_TECNICI)


def estrai_traduzioni(radice: Path, lingua: str) -> dict:
    modelli, campi, selezioni = {}, defaultdict(dict), defaultdict(dict)
    # Mappa generica originale -> tradotto: serve alle etichette dei filtri,
    # che nelle viste compaiono in inglese e sono tradotte altrove nel .po.
    dizionario = {}
    file_po = sorted(radice.glob(f"addons/*/i18n/{lingua}.po"))

    for percorso in file_po:
        for rif, msgid, msgstr in _blocchi_po(percorso):
            etichetta = msgstr or msgid          # non tradotto -> resta l'originale
            if not etichetta:
                continue
            if msgid and msgstr:
                dizionario.setdefault(msgid, msgstr)
            for riga in rif:
                m = RIF_MODELLO.match(riga)
                if m:
                    modelli.setdefault(m.group("modello"), {"it": etichetta, "en": msgid})
                    continue
                m = RIF_CAMPO.match(riga)
                if m:
                    campo = m.group("campo")
                    if _esposto(campo):
                        campi[m.group("modello")].setdefault(
                            campo, {"it": etichetta, "en": msgid}
                        )
                    continue
                m = RIF_SELEZIONE.match(riga)
                if m:
                    if not _esposto(m.group("campo")):
                        continue
                    chiave = f"{m.group('campo')}.{m.group('valore')}"
                    selezioni[m.group("modello")].setdefault(
                        chiave, {"it": etichetta, "en": msgid}
                    )
    return {
        "modelli": modelli,
        "campi": {k: v for k, v in campi.items()},
        "selezioni": {k: v for k, v in selezioni.items()},
        "dizionario": dizionario,
        "file_letti": len(file_po),
    }


def estrai_filtri(radice: Path, dizionario: dict) -> dict:
    """Filtri nominati nelle viste: categorie aziendali gia' curate (T5).

    Nelle viste l'etichetta e' in inglese; la traduzione si recupera dalla
    mappa generica del .po, dove compare come voce autonoma.
    """
    filtri = defaultdict(dict)
    for percorso in radice.glob("addons/*/views/*.xml"):
        modulo = percorso.parts[-3]
        testo = percorso.read_text(encoding="utf-8", errors="replace")
        for rx in (FILTRO, FILTRO_INV):
            for m in rx.finditer(testo):
                en = m.group("etichetta")
                filtri[modulo].setdefault(
                    m.group("nome"), {"it": dizionario.get(en, en), "en": en}
                )
    return {k: v for k, v in filtri.items()}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--core", default="../../core", help="radice dei sorgenti Odoo")
    p.add_argument("--lingua", default="it")
    p.add_argument("--out", default="lessico_l0.json")
    args = p.parse_args()

    radice = Path(args.core).resolve()
    if not (radice / "addons").is_dir():
        raise SystemExit(f"Sorgenti Odoo non trovati in {radice}")

    trad = estrai_traduzioni(radice, args.lingua)
    filtri = estrai_filtri(radice, trad["dizionario"])

    n_campi = sum(len(v) for v in trad["campi"].values())
    n_sel = sum(len(v) for v in trad["selezioni"].values())
    n_filtri = sum(len(v) for v in filtri.values())
    n_filtri_trad = sum(
        1 for v in filtri.values() for e in v.values() if e["it"] != e["en"]
    )

    risultato = {
        "lingua": args.lingua,
        "origine": str(radice),
        "statistiche": {
            "file_po": trad["file_letti"],
            "modelli": len(trad["modelli"]),
            "modelli_con_campi": len(trad["campi"]),
            "campi_esposti": n_campi,
            "valori_enumerati": n_sel,
            "filtri_nominati": n_filtri,
            "filtri_tradotti": n_filtri_trad,
        },
        "modelli": trad["modelli"],
        "campi": trad["campi"],
        "selezioni": trad["selezioni"],
        "filtri": filtri,
    }

    Path(args.out).write_text(
        json.dumps(risultato, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for chiave, valore in risultato["statistiche"].items():
        print(f"{chiave:24} {valore}")
    print(f"\nScritto in {args.out}")


if __name__ == "__main__":
    main()
