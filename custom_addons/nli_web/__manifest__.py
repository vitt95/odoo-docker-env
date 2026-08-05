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
    "depends": ["nli_dispatch", "web", "base_setup"],
    "data": [
        "views/aida_action.xml",
        "views/res_config_settings.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # **I token per primi, e per questo l'elenco non e' un glob.**
            #
            # Un pacchetto di risorse si compone nell'ordine in cui e' scritto, e
            # `--aida-*` deve esistere prima di ogni regola che lo legge. Con
            # `chat/**/*` l'ordine lo decideva l'alfabeto, che e' un ordine, ma non
            # e' *questo* ordine — e il giorno in cui un file nuovo si fosse chiamato
            # `aida_a...` sarebbe cambiato senza che nessuno lo avesse chiesto.
            "nli_web/static/src/aida_tokens.scss",
            # Il pannello: il contenitore, il pulsante nella barra, il servizio che
            # tiene lo stato quando nessuno guarda.
            "nli_web/static/src/panel/aida_service.js",
            "nli_web/static/src/panel/aida_panel.js",
            "nli_web/static/src/panel/aida_launcher.js",
            "nli_web/static/src/panel/aida_panel.xml",
            "nli_web/static/src/panel/aida_panel.scss",
            # La conversazione.
            "nli_web/static/src/chat/**/*",
        ],
    },
    "installable": True,
    "application": False,
}
