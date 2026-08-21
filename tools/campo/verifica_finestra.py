"""La decisione: si misura, o ci si ferma?

Zona pura — nessun Odoo, nessuna rete — perche' la parte che decide dev'essere provabile
senza accendere niente. `batteria.py` interroga il fornitore e passa qui i due numeri.

## Perche' esiste

Il 20 agosto 2026 il profilo dichiarava 8192 gettoni e il server ne serviva **4096**. I
prompt arrivavano al modello tagliati a meta' catalogo, il prodotto rispondeva
`not_understood`, e la cosa somigliava in tutto a un limite del modello. La firma del
taglio — `prompt_eval_count` fermo a 2050 — sta in un commento di `pipeline.py` da tre
settimane, e nessun controllo la leggeva.

Una misura presa contro una finestra sbagliata non e' una misura imprecisa: e' **carta
straccia che sembra un risultato**. E' il secondo modo di mentire di `ai/restart` §4, e
uno strumento di misura e' l'ultimo posto in cui dovrebbe stare.
"""

from __future__ import annotations

#: Si misura.
VAI = "vai"

#: Si misura, ma il fornitore non ha saputo dire quanto serve: chi legge il numero deve
#: saperlo. **Non e' un errore**: un fornitore che non espone la propria finestra e'
#: legittimo — `/api/ps` e' di `ollama`, non del protocollo — e fermarsi qui vorrebbe
#: dire che la batteria funziona con un fornitore solo.
NON_VERIFICABILE = "non verificabile"

#: Non si misura: i due numeri divergono e il risultato non direbbe niente di vero.
FERMATI = "fermati"


def esito_della_finestra(dichiarata: int, servita: int | None) -> str:
    """Che cosa fare, dati la finestra del profilo e quella che il fornitore serve."""
    if servita is None:
        return NON_VERIFICABILE
    return VAI if servita == dichiarata else FERMATI
