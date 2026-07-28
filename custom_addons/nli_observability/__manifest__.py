{
    "name": "AIDA Observability",
    "summary": "Interaction registry, quality metrics and corpus execution.",
    "version": "18.0.1.0.0",
    "category": "Productivity/Conversational",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    # Depends on the core only. Peripheral modules never depend on each other:
    # the registry observes the contract, not the components.
    "depends": ["nli_core"],
    "installable": True,
    "application": False,
}
