{
    "name": "AIDA Semantics",
    "summary": "Semantic dictionary, catalogue construction and reference resolution.",
    "version": "18.0.1.0.0",
    "category": "Productivity/Conversational",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    # Depends on the core only. It knows the customer's data and terminology
    # (D57: the catalogue is confidential information) and never talks to a
    # model provider — that separation is the point of `04` §6.3.
    "depends": ["nli_core"],
    "data": ["security/ir.model.access.csv"],
    "installable": True,
    "application": False,
}
