Progetto AIDA — NLIL per Odoo 18. Repo ~/Learning/odoo, branch ai-agent.

Prima di qualunque cosa leggi questi due file, sono il punto di ripresa dichiarato:
- ai/00-registro-decisioni.md — cosa è deciso. Il changelog in fondo è la cronologia
  reale; §13–§16 sono le questioni emerse implementando e le delibere di D87–D91.
- ai/12-piano-implementazione.md — §5 tabella di avanzamento, §5.1 come si verifica
  (comandi, fatti d'ambiente, i tre generi di zona architetturale).

Poi esegui ./manage.sh check per confermare che parti da verde.

Stato: parti 1–4 complete, parte 5 implementata ma con il profilo NON qualificato
(accuratezza 15% su qwen2.5 7B locale, sotto D44 su ogni sezione, quindi D80 rifiuta
l'attivazione — comportamento voluto). Prossima: parte 6, esecuzione asincrona.

Come lavoriamo:
- sei il Senior Staff Engineer, io l'Architect. Ti ho delegato l'autorità decisionale
  caso per caso: quando trovi una lacuna o una contraddizione nei documenti, analizzala,
  delibera e registrala in ai/00 con la sua argomentazione. Niente domande bloccanti;
  decidi e vai, tranne per le azioni distruttive.
- cerca sempre prima l'opzione che NON modifica il contratto, e scartala solo con un
  argomento. È così che è stata deliberata D87.
- nessun controllo può passare a vuoto: ogni verifica dichiara quanto ha ispezionato e
  l'ispezione vuota è un fallimento. Ogni controllo ha un test che lo mostra scattare.
- niente deroghe inline: allentare una regola richiede una decisione numerata in ai/00.
- riporta gli esiti come sono, con i numeri. Un numero brutto misurato vale più di un
  numero bello asserito.

Due cose in sospeso prima di iniziare:
1. ai/12-piano-implementazione.md ha la sezione §5.1 non committata — committala.
2. D93 è una mia proposta in attesa di delibera (ai/00 §16.4): la guardia
   attributo/entità in Fase A, con la misura già fatta. Dimmi tu se la approvo.

Parte 6 — esecuzione asincrona. Contenuto e decisioni sono in ai/12 §Parte 6:
accettazione immediata + ir.cron._trigger() + notifica su bus (D20a), un solo cron
dispatcher con pool derivato da db_maxconn (D20b, §6.4 del registro), i cinque limiti
di carico con rifiuto esplicito (D20c), dispatcher differito separato (D20d),
messaggi di rifiuto per carico (D69), e il contesto societario ricostruito dal turno
(D40) — che nella parte 4 è già persistito e va usato qui.

Il vincolo che conta: nessun percorso privilegiato, nemmeno nel dispatcher.

Sul criterio di completamento (D27, prova di isolamento) sii onesto: costruisci
l'arnese di misura e riporta il numero dichiarando su cosa l'hai misurato. Questo
portatile con un db vuoto non è un'installazione rappresentativa, e chiamarla
«prova passata» sarebbe falso.

Procedi.

Se invece vuoi solo che continui senza rileggere tutto, basta questo:

Riprendi il progetto AIDA: leggi ai/00-registro-decisioni.md e
ai/12-piano-implementazione.md, verifica con ./manage.sh check, poi vai con la parte 6.
Stesse regole di prima: deliberi tu le questioni che emergono e le registri in ai/00.

Due note su perché il prompt lungo è fatto così. Le regole di lavoro sono dentro perché sono la parte che una sessione fredda perde per prima: senza «cerca l'opzione che non modifica il contratto» avrei approvato D87 senza cercare l'opzione G, e G era quella tentante. E il paragrafo su D27 è lì di proposito: è il punto in cui sarebbe comodo scrivere «prova superata» su una misura fatta su un portatile, e volevo che il vincolo arrivasse dal prompt invece di dipendere dalla mia memoria.