Hospital Management Theme OWL
=============================

A safe Odoo 18 UI theme extension for ``base_hospital_management``.

This module does not edit any original file from the base module. General styling
and Owl behavior are applied through backend/frontend assets, while narrowly
scoped inherited views stabilize the enterprise patient form and provide the
patient and blood-bank detail cards.
The base business models, actions, menus, access rules, and workflows remain
unchanged.

Implemented features
--------------------

* Modern hospital SaaS visual system with blue/teal palette.
* Scoped backend styling activated only on hospital screens.
* Responsive styling for form, list, kanban, calendar, search, control panel,
  statusbar, notebook, chatter, and dashboard screens.
* Owl quick action panel registered through the webclient main_components
  registry.
* Static dashboard template extensions for Reception, Doctor, Lab, and Pharmacy
  dashboards.
* Odoo 18-compatible patient and blood-bank kanban detail cards.
* Frontend/portal styling for patient and booking pages.

No changes are made to:

* Python models
* Business workflows
* Menus/actions
* Security/access rules
* Database schema
* Original ``base_hospital_management`` files


18.0.1.0.15
-------------
* Fixed the oversized duplicate-looking linked-user avatar on the hospital Staff kanban.
* Restored Odoo's native inline avatar dimensions after the generic kanban image rule expanded it.
* Hid only the redundant linked-user avatar on hospital Staff cards while preserving the employee image, presence indicator, activity icon, role grouping, and card content.
* Kept all models, actions, domains, menus, access rules, and workflows unchanged.


18.0.1.0.14
-------------
* Restored native side-by-side form groups by removing the theme-level horizontal ``column-gap`` that forced Odoo's 50% columns to wrap.
* Reorganized the Enterprise Patient Profile clinical summary into two responsive inner groups so desktop form space is used efficiently.
* Preserved all patient fields, placeholders, notebook pages, workflows, and business logic.


18.0.1.0.13
-------------
* Removed patient-kanban sample records that rendered as empty placeholder cards.
* Disabled patient kanban quick-create placeholders.
* Removed the double-card wrapper effect from the custom hospital detail kanbans.
* Moved hover styling to the visible hospital card surface.

18.0.1.0.12
-------------
* Replaced the legacy ``kanban_image()`` call with the Odoo 18 image field widget.
* Replaced obsolete ``quick_add`` with ``quick_create`` on blood-bank kanban.
* Removed a FontAwesome 5-only icon and browser ``:has()`` selector dependencies.
* Debounced hospital-screen detection and reduced MutationObserver work.
* Stabilized responsive kanban sizing, quick-panel storage, and accessibility.

18.0.1.0.9
------------
* Hid the floating Hospital Quick Actions panel on dashboard screens while keeping it available on operational forms, lists, and kanban screens.

18.0.1.0.7
------------
* Removed CSS min()/clamp() expressions that can fail Odoo/Sass bundle compilation when px and vw/rem units are mixed.
* Fixed backend form alignment for patient and clinical forms.
* Restored stat-button, avatar, statusbar, and chatter alignment.
