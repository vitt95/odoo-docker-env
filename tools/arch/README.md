# Controlli automatici dei confini

Realizzazione della decisione **D24** — i quattro controlli di
`ai/04-architettura.md` §6.4, richiesti nella prima consegna e non rinviabili.

## Perché esistono

`04` §6.1 lo dice in una riga: *un'architettura descritta in un documento è una
convenzione*. Le convenzioni si erodono sotto pressione, e l'erosione non produce
errori — produce numeri diversi, tutti plausibili. Questi controlli trasformano
cinque righe di progettazione in cinque proprietà verificabili a ogni push.

La delibera di D24 chiarisce anche perché arrivano **prima** del prodotto:
costano poco adesso e in modo superlineare dopo, quando le violazioni esistono e
vanno prima sanate.

## Come si eseguono

```bash
python3 tools/arch/run.py                 # i quattro controlli, exit code 0/1
python3 -m unittest discover -s tools/arch/tests -t .   # i test dei controlli
./manage.sh check                         # entrambi
./manage.sh test <db>                     # entrambi + suite Odoo sullo scheletro
./scripts/install-hooks.sh                # abilita il pre-push
```

Tre punti di esecuzione automatica, indipendenti fra loro: `pre-push`,
`.github/workflows/boundaries.yml`, `./manage.sh test`. Solo librerie standard:
un controllo che richiede il proprio ambiente è un controllo che qualcuno salta.

## I quattro controlli

| Controllo | File | Verifica | Protegge |
|---|---|---|---|
| **Manifest** | `check_manifest.py` | Il grafo dichiarato nei `__manifest__.py` è quello di `04` §6.2, esattamente | D18 |
| **Importazioni** | `check_imports.py` | Nessun modulo importa oltre le proprie dipendenze; solo `nli_engine` importa librerie di fornitore e di rete | D18, V5, V7 |
| **Sintattico** | `check_syntax.py` | Nessun accesso diretto a PostgreSQL; nessuna elevazione di privilegio | V3, V2 |
| **Architetturale** | `check_purity.py` + `nli_core/tests/` | Le zone pure non importano la piattaforma e non leggono l'orologio | D9, D82, D11 |

`spec.py` contiene **tutte** le regole; i quattro moduli contengono solo la
meccanica per trovarle. Confrontare `spec.py` con `04` §6.2–6.3 è un diff, non
una lettura.

## Due proprietà volute

**Nessun meccanismo di deroga.** Una regola derogabile in linea è di nuovo una
convenzione. Derogare richiede una nuova decisione nel registro, numerata da
**D87**: rimuovere un vincolo è modificare la decisione, non semplificarla
(`00` §10).

**Nessun controllo può passare a vuoto.** Ogni controllo dichiara quanto ha
ispezionato e il runner tratta l'ispezione vuota come un fallimento. È la
modalità di guasto più probabile di questo genere di strumenti: uno controllo che
non trova più i file da esaminare riporta successo per sempre, e nessuno se ne
accorge perché la pipeline è verde. Per la stessa ragione una zona pura
dichiarata e assente è una violazione, non un non-problema.

## La divisione di lavoro con i test Odoo

| Dove | Che cosa afferma | Serve un database |
|---|---|---|
| `tools/arch/` | Il grafo **dichiarato** è il grafo **progettato**. Unico luogo dove il progetto è trascritto | No |
| `custom_addons/nli_core/tests/test_boundaries.py` | Il sistema **in esecuzione** corrisponde ai manifest che ha caricato, e i cinque moduli si installano | Sì |

La seconda metà non ripete il progetto: lo rilegge dai manifest attraverso l'API
di Odoo. Per questo le due non possono divergere.

La parte comportamentale del quarto controllo — l'Applicatore puro su ingressi
reali, il Validatore sempre attraversato, il Presentatore che riceve stato e
risultato insieme — arriva con i componenti, nelle parti 2 e 4.

## Estenderli

Aggiungere una regola: si modifica `spec.py` e si aggiunge il caso in
`tests/test_checks.py` che la mostra scattare. Un controllo mai visto fallire è
indistinguibile da un controllo che non può fallire — ed è il motivo per cui i
test delle fixture esistono prima del prodotto.
