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

`serve` elenca le parole che il catalogo deve contenere perche' la frase sia
rispondibile. Se mancano, il caso e' **saltato** invece che contato come sbagliato: con
la finestra a 4096 il budget di **D79** tiene 17 attributi su 66 (`00` §39.5), e
addossare al modello un attributo che nessuno gli ha mostrato falserebbe la misura nella
direzione peggiore — quella che fa lavorare sul pezzo giusto per il motivo sbagliato.
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
     ("telefono",)),
    (INTENTI, "cerca i lead che hanno milano nel nome", {"condizioni": 1},
     ("nome",)),
    (INTENTI, "quanti lead ci sono", {"misure": {"count"}}, ()),
    (INTENTI, "dammi il numero di lead di oggi",
     {"misure": {"count"}, "periodo": True}, ()),
    (INTENTI, "dammi il numero di lead per stato",
     {"misure": {"count"}, "raggruppa": 1}, ("stato",)),
    (INTENTI, "dammi il numero di lead per stato che sono stati creati quest'anno",
     {"misure": {"count"}, "raggruppa": 1, "periodo": True},
     ("stato", "data di creazione")),
    (INTENTI, "qual e' il ricavo atteso medio dei lead",
     {"misure": {"avg"}}, ("ricavo atteso",)),
    (INTENTI, "somma il ricavo atteso dei lead", {"misure": {"sum"}},
     ("ricavo atteso",)),
    (INTENTI, "qual e' il ricavo atteso piu' alto", {"misure": {"max"}},
     ("ricavo atteso",)),
    (INTENTI, "qual e' il ricavo atteso piu' basso", {"misure": {"min"}},
     ("ricavo atteso",)),
    (INTENTI, "il ricavo atteso medio per stato",
     {"misure": {"avg"}, "raggruppa": 1}, ("stato", "ricavo atteso")),
    (INTENTI, "quanti lead per stato e per commerciale",
     {"misure": {"count"}, "raggruppa": 2}, ("stato", "commerciale")),
    (INTENTI, "i lead ordinati per ricavo atteso", {"ordina": 1},
     ("ricavo atteso",)),
    (INTENTI, "i 10 lead con il ricavo atteso piu' alto",
     {"ordina": 1, "limite": 10}, ("ricavo atteso",)),
    (INTENTI, "i primi 5 lead", {"limite": 5}, ()),
    (INTENTI, "i lead che hanno un commerciale", {"condizioni": 1},
     ("commerciale",)),
    (INTENTI, "i lead senza commerciale", {"condizioni": 1}, ("commerciale",)),

    # -- OPERATORI -------------------------------------------------------------
    (OPERATORI, "i lead con ricavo atteso uguale a 1000", {"condizioni": 1},
     ("ricavo atteso",)),
    (OPERATORI, "i lead con ricavo atteso sopra 1000", {"condizioni": 1},
     ("ricavo atteso",)),
    (OPERATORI, "i lead con ricavo atteso sotto 1000", {"condizioni": 1},
     ("ricavo atteso",)),
    (OPERATORI, "i lead con ricavo atteso di almeno 1000", {"condizioni": 1},
     ("ricavo atteso",)),
    (OPERATORI, "i lead con ricavo atteso al massimo di 1000", {"condizioni": 1},
     ("ricavo atteso",)),
    (OPERATORI, "i lead con ricavo atteso fra 1000 e 5000", {"condizioni": 1},
     ("ricavo atteso",)),
    (OPERATORI, "i lead che contengono spa nel nome", {"condizioni": 1},
     ("nome",)),
    (OPERATORI, "i lead che iniziano per ross", {"condizioni": 1}, ("nome",)),
    (OPERATORI, "i lead senza email", {"condizioni": 1}, ("email",)),
    (OPERATORI, "i lead che hanno una email", {"condizioni": 1}, ("email",)),
    (OPERATORI, "i lead sopra 1000 e senza commerciale", {"condizioni": 2},
     ("ricavo atteso", "commerciale")),
    (OPERATORI, "i lead sopra 1000 oppure senza email", {"condizioni": 2},
     ("ricavo atteso", "email")),

    # -- DATE ------------------------------------------------------------------
    # Su `crm.lead` le date esposte sono piu' d'una, quindi una frase che non ne
    # nomina nessuna deve finire in una domanda: e' **D135**, ed e' l'esito giusto,
    # non un fallimento.
    (DATE, "i lead di oggi", {"esito": "clarification"}, ()),
    (DATE, "i lead creati oggi", {"periodo": True}, ("data di creazione",)),
    (DATE, "i lead creati ieri", {"periodo": True}, ("data di creazione",)),
    (DATE, "i lead creati questa settimana", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati la settimana scorsa", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati questo mese", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati il mese scorso", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati negli ultimi 7 giorni", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati negli ultimi 30 giorni", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati negli ultimi 90 giorni", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati quest'anno", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati l'anno scorso", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati questo trimestre", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati il trimestre scorso", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati da inizio anno", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati prima di questo mese", {"periodo": True},
     ("data di creazione",)),
    (DATE, "i lead creati dopo il mese scorso", {"periodo": True},
     ("data di creazione",)),
    (DATE, "quanti lead creati oggi", {"misure": {"count"}, "periodo": True},
     ("data di creazione",)),

    # -- LIMITI DICHIARATI -----------------------------------------------------
    # Queste frasi chiedono cose che il contratto **non ammette** (`ai/17` §3, e la
    # classe `TestQuelloCheNonSiPuoDire` del banco). L'esito giusto e' un rifiuto
    # onesto o una domanda: cio' che non deve succedere e' una risposta plausibile.
    # Si contano a parte, e un `operations` qui e' un **allarme**, non un successo.
    (LIMITI, "gli stati con piu' di 10 lead", {"esito": "clarification"},
     ("stato",)),
    (LIMITI, "i secondi 20 lead", {"esito": "clarification"}, ()),
    (LIMITI, "esportami i lead in excel", {"esito": "out_of_scope"}, ()),
    (LIMITI, "i lead che non sono di milano", {"esito": "clarification"},
     ("citta'",)),
    (LIMITI, "i lead creati nel primo trimestre", {"esito": "clarification"},
     ("data di creazione",)),
    (LIMITI, "i lead creati a gennaio", {"esito": "clarification"},
     ("data di creazione",)),
]
