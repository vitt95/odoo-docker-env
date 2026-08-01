"""Registry, metrics and corpus execution (`ai/07-piano-valutazione-qualita.md`).

Three constraints apply here before any feature does: utterances are never
persisted in clear (D54), utterances and catalogues never reach diagnostic logs
(D60), and no report exposes accuracy without coverage (`07` §5.4). Retention
deletion runs in bounded batches on the deferred dispatcher, never on the
interactive pool (D26).
"""
