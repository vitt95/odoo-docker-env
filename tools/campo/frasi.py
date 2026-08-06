"""Le frasi della batteria sul campo: ogni operazione di `ai/16`, detta da una persona.

## A cosa serve questo file, e a cosa **non** serve

`custom_addons/nli_core/tests/test_capabilities.py` prova che il prodotto **sa fare**
ogni operazione di `ai/16`: parte da uno stato e arriva ai numeri, e' deterministico,
gira in un secondo e sta nella suite. Quello che non puo' dire e' se una persona
riesce a **chiederle**.

Qui ci sono le stesse operazioni scritte come le direbbe qualcuno in chat. Non e' una
prova: e' una **misura**. Il modello non e' deterministico — la stessa frase il
3 agosto 2026 ha dato 39 record la mattina e `not_understood` il pomeriggio — quindi il
risultato di un giro e' una fotografia, non un verdetto, e va confrontato con altri
giri e non preso da solo.

## Come si legge un'attesa

Un'attesa **non nomina i riferimenti** del catalogo, e non e' pigrizia: i `ref`
dipendono dall'installazione, e una batteria che li fissasse misurerebbe questa banca
dati invece del prodotto. Si guarda la **forma** di cio' che e' uscito — c'e' un
raggruppamento? c'e' una misura di conteggio? c'e' una condizione temporale? — che e'
esattamente cio' che la frase chiede.

`serve` elenca i **riferimenti** del catalogo che devono essere esposti perche' la
frase sia rispondibile — `crm_lead.user_id`, non «commerciale». Se mancano, il caso e'
**saltato** invece che contato come sbagliato: con la finestra a 4096 il budget di
**D79** tiene 17 attributi su 66 (`00` §39.5), e addossare al modello un attributo che
nessuno gli ha mostrato falserebbe la misura nella direzione peggiore — quella che fa
lavorare sul pezzo giusto per il motivo sbagliato.

**Perche' i `ref` e non le parole.** Qui c'erano le parole, ed erano quelle che una
persona direbbe: «data di creazione», «email», «commerciale». Il filtro le confrontava
con le etichette Odoo vere — `Data creazione`, `E-mail`, `Addetto vendite` — e non si
incontravano: 21 frasi su 54, tutte le date, non sono mai state eseguite in nessun giro
(`ai/restart.md` §4). Peggio: fra le saltate c'erano frasi a cui il prodotto risponde
**giusto**, perche' il modello quelle parole le collega da solo alle etichette. Il
`ref` toglie di mezzo la traduzione a mano: e' cio' che il catalogo pubblica.

Questo non contraddice la regola qui sopra — un'**attesa** continua a non nominare
riferimenti. `serve` non e' un'attesa: non dice cosa deve uscire, dice cosa il modello
deve aver visto per poter rispondere, e quello e' un fatto del catalogo.

I riferimenti sono di `crm_lead` perche' le frasi parlano di lead. Su una banca dati
senza CRM la batteria si ferma e lo dice, invece di ripiegare su un'altra entita'.
"""

#: Le famiglie, nell'ordine di `ai/16`.
INTENTI = "intenti"
OPERATORI = "operatori"
DATE = "date"
LIMITI = "limiti"

#: Una frase e cosa deve uscirne. Chiavi ammesse in `attesa`:
#:
#: * `esito`      — "operations" (predefinito) o "clarification";
#: * `misure`     — le funzioni di aggregazione attese, per nome;
#: * `raggruppa`  — quanti raggruppamenti;
#: * `ordina`     — quanti ordinamenti;
#: * `limite`     — il valore del limite, quando la frase lo dice;
#: * `condizioni` — quante condizioni nel filtro;
#: * `periodo`    — True se una condizione deve portare un'espressione di tempo;
#: * `colonne`    — quante colonne esplicite.
FRASI = [
    # -- INTENTI ---------------------------------------------------------------
    (INTENTI, "mostrami i lead", {}, ()),
    (INTENTI, "mostrami i lead con nome e telefono", {"colonne": 2},
     ("crm_lead.phone",)),
    (INTENTI, "cerca i lead che hanno milano nel nome", {"condizioni": 1},
     ("crm_lead.name",)),
    (INTENTI, "quanti lead ci sono", {"misure": {"count"}}, ()),
    (INTENTI, "dammi il numero di lead di oggi",
     {"misure": {"count"}, "periodo": True}, ()),
    # **«per stato» e' una trappola, e va guardata.** Sul catalogo vero di `crm_lead`
    # `Stato` e' `state_id`, cioe' la **provincia**, mentre la fase di vendita si
    # chiama `Fase` (`stage_id`). Chi ha scritto queste frasi intendeva la fase, e
    # `serve` dichiara `stage_id`; ma l'attesa conta *quanti* raggruppamenti, non su
    # cosa, quindi un raggruppamento per provincia passerebbe lo stesso. Sono due
    # decisioni da prendere insieme all'Architect: se la frase va detta «per fase», e
    # se l'attesa debba nominare il riferimento del raggruppamento almeno qui.
    (INTENTI, "dammi il numero di lead per stato",
     {"misure": {"count"}, "raggruppa": 1}, ("crm_lead.stage_id",)),
    (INTENTI, "dammi il numero di lead per stato che sono stati creati quest'anno",
     {"misure": {"count"}, "raggruppa": 1, "periodo": True},
     ("crm_lead.stage_id", "crm_lead.create_date")),
    (INTENTI, "qual e' il ricavo atteso medio dei lead",
     {"misure": {"avg"}}, ("crm_lead.expected_revenue",)),
    (INTENTI, "somma il ricavo atteso dei lead", {"misure": {"sum"}},
     ("crm_lead.expected_revenue",)),
    (INTENTI, "qual e' il ricavo atteso piu' alto", {"misure": {"max"}},
     ("crm_lead.expected_revenue",)),
    (INTENTI, "qual e' il ricavo atteso piu' basso", {"misure": {"min"}},
     ("crm_lead.expected_revenue",)),
    (INTENTI, "il ricavo atteso medio per stato",
     {"misure": {"avg"}, "raggruppa": 1}, ("crm_lead.stage_id", "crm_lead.expected_revenue")),
    (INTENTI, "quanti lead per stato e per commerciale",
     {"misure": {"count"}, "raggruppa": 2}, ("crm_lead.stage_id", "crm_lead.user_id")),
    (INTENTI, "i lead ordinati per ricavo atteso", {"ordina": 1},
     ("crm_lead.expected_revenue",)),
    (INTENTI, "i 10 lead con il ricavo atteso piu' alto",
     {"ordina": 1, "limite": 10}, ("crm_lead.expected_revenue",)),
    (INTENTI, "i primi 5 lead", {"limite": 5}, ()),
    (INTENTI, "i lead che hanno un commerciale", {"condizioni": 1},
     ("crm_lead.user_id",)),
    (INTENTI, "i lead senza commerciale", {"condizioni": 1}, ("crm_lead.user_id",)),

    # -- OPERATORI -------------------------------------------------------------
    (OPERATORI, "i lead con ricavo atteso uguale a 1000", {"condizioni": 1},
     ("crm_lead.expected_revenue",)),
    (OPERATORI, "i lead con ricavo atteso sopra 1000", {"condizioni": 1},
     ("crm_lead.expected_revenue",)),
    (OPERATORI, "i lead con ricavo atteso sotto 1000", {"condizioni": 1},
     ("crm_lead.expected_revenue",)),
    (OPERATORI, "i lead con ricavo atteso di almeno 1000", {"condizioni": 1},
     ("crm_lead.expected_revenue",)),
    (OPERATORI, "i lead con ricavo atteso al massimo di 1000", {"condizioni": 1},
     ("crm_lead.expected_revenue",)),
    (OPERATORI, "i lead con ricavo atteso fra 1000 e 5000", {"condizioni": 1},
     ("crm_lead.expected_revenue",)),
    (OPERATORI, "i lead che contengono spa nel nome", {"condizioni": 1},
     ("crm_lead.name",)),
    (OPERATORI, "i lead che iniziano per ross", {"condizioni": 1}, ("crm_lead.name",)),
    (OPERATORI, "i lead senza email", {"condizioni": 1}, ("crm_lead.email_from",)),
    (OPERATORI, "i lead che hanno una email", {"condizioni": 1}, ("crm_lead.email_from",)),
    (OPERATORI, "i lead sopra 1000 e senza commerciale", {"condizioni": 2},
     ("crm_lead.expected_revenue", "crm_lead.user_id")),
    (OPERATORI, "i lead sopra 1000 oppure senza email", {"condizioni": 2},
     ("crm_lead.expected_revenue", "crm_lead.email_from")),

    # -- DATE ------------------------------------------------------------------
    # Su `crm.lead` le date esposte sono piu' d'una, quindi una frase che non ne
    # nomina nessuna deve finire in una domanda: e' **D135**, ed e' l'esito giusto,
    # non un fallimento.
    (DATE, "i lead di oggi", {"esito": "clarification"}, ()),
    (DATE, "i lead creati oggi", {"periodo": True}, ("crm_lead.create_date",)),
    (DATE, "i lead creati ieri", {"periodo": True}, ("crm_lead.create_date",)),
    (DATE, "i lead creati questa settimana", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati la settimana scorsa", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati questo mese", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati il mese scorso", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati negli ultimi 7 giorni", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati negli ultimi 30 giorni", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati negli ultimi 90 giorni", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati quest'anno", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati l'anno scorso", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati questo trimestre", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati il trimestre scorso", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati da inizio anno", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati prima di questo mese", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "i lead creati dopo il mese scorso", {"periodo": True},
     ("crm_lead.create_date",)),
    (DATE, "quanti lead creati oggi", {"misure": {"count"}, "periodo": True},
     ("crm_lead.create_date",)),

    # -- LIMITI DICHIARATI -----------------------------------------------------
    # Queste frasi chiedono cose che il contratto **non ammette** (`ai/17` §3, e la
    # classe `TestQuelloCheNonSiPuoDire` del banco). L'esito giusto e' un rifiuto
    # onesto o una domanda: cio' che non deve succedere e' una risposta plausibile.
    # Si contano a parte, e un `operations` qui e' un **allarme**, non un successo.
    (LIMITI, "gli stati con piu' di 10 lead", {"esito": "clarification"},
     ("crm_lead.stage_id",)),
    (LIMITI, "i secondi 20 lead", {"esito": "clarification"}, ()),
    (LIMITI, "esportami i lead in excel", {"esito": "out_of_scope"}, ()),
    (LIMITI, "i lead che non sono di milano", {"esito": "clarification"},
     ("crm_lead.city",)),
    (LIMITI, "i lead creati nel primo trimestre", {"esito": "clarification"},
     ("crm_lead.create_date",)),
    (LIMITI, "i lead creati a gennaio", {"esito": "clarification"},
     ("crm_lead.create_date",)),
]
