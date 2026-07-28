{
    "name": "AIDA Web",
    "summary": "Conversational channel and result presentation inside Odoo.",
    "version": "18.0.1.0.0",
    "category": "Productivity/Conversational",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    # Reaches the core through nli_semantics, per the graph of 04 §6.2.
    # `ui_brand_tokens` is deliberately NOT a dependency: D25 requires the
    # tokens to be used when present and the interface to degrade gracefully
    # when they are not.
    "depends": ["nli_dispatch", "web"],
    "installable": True,
    "application": False,
}
