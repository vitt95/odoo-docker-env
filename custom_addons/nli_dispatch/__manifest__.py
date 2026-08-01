{
    "name": "AIDA — Dispatch",
    "summary": "Asynchronous execution: acceptance, queue, dispatcher, load control",
    "version": "18.0.1.0.0",
    "category": "Productivity",
    "author": "AIDA",
    "license": "LGPL-3",
    # The composition root of the interrogation chain (D94). It is the one module
    # that may know both who builds the catalogue (`nli_semantics`) and who talks to
    # the model (`nli_engine`): the chain of `05` §3.3 needs both, and neither of
    # them may depend on the other (§6.3).
    #
    # `bus` is the platform dependency of D20a: the notification is served by the
    # gevent process, which is what keeps a waiting client off the HTTP workers (F3).
    "depends": ["nli_semantics", "nli_engine", "bus"],
    "data": [
        "security/ir.model.access.csv",
        "security/nli_dispatch_security.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}
