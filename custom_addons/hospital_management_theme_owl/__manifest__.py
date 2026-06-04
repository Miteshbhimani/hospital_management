# -*- coding: utf-8 -*-
{
    "name": "Hospital Management Theme OWL",
    "summary": "Modern OWL/SCSS UI theme extension for Base Hospital Management",
    "version": "18.0.1.0.11",
    "category": "Services/Healthcare",
    "author": "Custom Development",
    "website": "https://www.odoo.com",
    "license": "LGPL-3",
    "depends": [
        "web",
        "base_hospital_management",
    ],
    # No database view inheritance is loaded. The base module has unstable/missing
    # view XML IDs in some installations; this theme is therefore applied safely
    # through backend/frontend assets only.
    "data": [
        "views/hospital_kanban_detail_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hospital_management_theme_owl/static/src/scss/hospital_theme_variables.scss",
            "hospital_management_theme_owl/static/src/scss/hospital_backend_theme.scss",
            "hospital_management_theme_owl/static/src/xml/hospital_theme_components.xml",
            "hospital_management_theme_owl/static/src/xml/hospital_dashboard_templates_inherit.xml",
            "hospital_management_theme_owl/static/src/js/theme_detector.js",
            "hospital_management_theme_owl/static/src/js/quick_panel.js",
        ],
        "web.assets_frontend": [
            "hospital_management_theme_owl/static/src/scss/hospital_portal_theme.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
