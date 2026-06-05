# -*- coding: utf-8 -*-
{
    "name": "Hospital Management Theme OWL",
    "summary": "Modern OWL/SCSS UI theme extension for Base Hospital Management",
    "version": "18.0.1.0.15",
    "category": "Services/Healthcare",
    "author": "Custom Development",
    "website": "https://www.odoo.com",
    "license": "LGPL-3",
    "depends": [
        "web",
        "base_hospital_management",
    ],
    # General styling and OWL behavior are asset-based. Database inheritance is
    # intentionally limited to one patient-form layout and two hospital kanbans.
    "data": [
        "views/hospital_form_layout_views.xml",
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
