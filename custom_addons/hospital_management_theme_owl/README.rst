Hospital Management Theme OWL
=============================

A safe Odoo 18 UI theme extension for ``base_hospital_management``.

This module intentionally does not edit or inherit database views from the base
module. Some base installations contain unstable or missing view XML IDs, and
Odoo validates inherited views during module installation. The theme is therefore
applied through backend/frontend assets, Owl components, SCSS, and static QWeb
inheritance of the base dashboard templates.

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
* Frontend/portal styling for patient and booking pages.

No changes are made to:

* Python models
* Business workflows
* Menus/actions
* Security/access rules
* Database schema
* Original ``base_hospital_management`` files


18.0.1.0.7
----------
- Removed CSS min()/clamp() expressions that can fail Odoo/Sass bundle compilation when px and vw/rem units are mixed.
- Kept the module asset-only; no database view inheritance is loaded.


18.0.1.0.7
-----------
* Fixed backend form alignment for patient and clinical forms.
* Removed full-width pill styling from Odoo form headers/statusbars.
* Restored stat-button/avatar placement inside the form sheet.
* Aligned chatter width with the form sheet.


Version 18.0.1.0.9
------------------
- Hides the floating Hospital Quick Actions panel on all hospital dashboard screens while keeping it available on operational forms, lists, and kanban screens.
