# -*- coding: utf-8 -*-
{
    "name": "Hospital Staff Access Management",
    "summary": "Create hospital staff and separate manager-only hospital access-rights menus",
    "version": "18.0.1.6.0",
    "category": "Services/Healthcare",
    "author": "Custom Development",
    "license": "LGPL-3",
    "depends": [
        "base_hospital_management",
        "hr",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/hospital_staff_access_views.xml",
        "views/hospital_access_right_views.xml",
        "wizards/hospital_staff_access_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
