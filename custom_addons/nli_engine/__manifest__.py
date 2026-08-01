{
    "name": "AIDA Engine",
    "summary": "Interpreter and model provider adapters.",
    "version": "18.0.1.0.0",
    "category": "Productivity/Conversational",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    # The only module allowed to import provider and network libraries, and the
    # only one that talks to a model. It does not depend on nli_semantics: it
    # receives the catalogue, it does not build it (04 §6.3).
    "depends": ["nli_core"],
    "data": ["security/ir.model.access.csv"],
    "installable": True,
    "application": False,
}
