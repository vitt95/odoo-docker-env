{
    "name": "UI Brand Tokens",
    "summary": "Design tokens (--pui-* CSS variables + $o-* overrides) for the Premium skin.",
    "version": "18.0.1.0.0",
    "category": "Themes/Backend",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    "depends": ["web"],
    # No assets bundle here: token source files are consumed by
    # ui_theme_engine's Premium bundle. This module only ships the sources.
    "installable": True,
    "application": False,
}
