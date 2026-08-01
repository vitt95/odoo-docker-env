{
    "name": "AIDA Core",
    "summary": "Interrogation contract, state, validation, application and execution.",
    "version": "18.0.1.0.0",
    "category": "Productivity/Conversational",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    # Root of the dependency graph of `ai/04-architettura.md` §6.2. The core
    # knows neither the providers (V5) nor the channels (P5): every other
    # nli_* module depends on it, and it depends on none of them.
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "security/nli_security.xml",
    ],
    "installable": True,
    "application": False,
}
