# Hospital Accounting Management — Accounting Extraction and Integration Blueprint

## Final module boundary

The Hospital codebase now uses a strict separation of concerns:

- `base_hospital_management` contains only hospital operational workflows such as patients, OPD, IPD, admissions, prescriptions, laboratory operations, pharmacy sale orders, rooms, beds, and insurance master data.
- `hospital_accounting_management` contains all accounting-specific behavior and depends on both `base_hospital_management` and native Odoo Accounting.

The base module no longer imports, inherits, or directly references `account.move`, `account.move.line`, `account.payment.register`, `account.tax`, or the removed `inpatient.payment` model.

## Legacy accounting code removed from the base module

Removed from `base_hospital_management`:

- Direct OPD invoice creation and invoice smart-button logic.
- Direct IPD invoice creation and draft invoice-line aggregation.
- Direct laboratory invoice creation and invoice counter logic.
- Patient invoice smart button and `account.move` action.
- `account.payment.register` override.
- Legacy `inpatient.payment` shadow-payment model and its ACL entries.
- Accounting tax fields from laboratory core models and views.
- Accounting-specific invoice/payment UI elements from OPD, IPD, patient lab test, and patient forms.
- Direct `account.move` lookup from the patient portal controller.

## Accounting behavior owned by the separate module

`hospital_accounting_management` now provides:

- Native customer invoices using `account.move` and `account.move.line`.
- OPD, IPD, and laboratory invoice workflows.
- Native payment registration through `account.payment.register`.
- Patient financial summaries and hospital invoice navigation.
- Hospital invoice metadata, source links, department, doctor, and service classification.
- Accounting products and tax mappings for consultations, rooms, beds, lab tests, and radiology.
- Insurance accounting configuration fields.
- Hospital finance security groups and menus.
- IPD `hospital.inpatient.charge` lines for billable procedures and services.

`hospital.inpatient.charge` replaces the misleading legacy `inpatient.payment` model. Charge lines represent services to invoice; actual payments remain exclusively in native Odoo Accounting.

## Data preservation and upgrade notes

Existing OPD/IPD/Lab invoice-link columns are preserved by defining the same field names in `hospital_accounting_management`. Upgrade both modules together so those columns remain registered and their values remain accessible.

The removed `inpatient.payment` table is not used by the new code. Before production upgrade, export any meaningful legacy rows and import them as `hospital.inpatient.charge` records when they represent billable services. Do not migrate them as payments unless they correspond to real posted Accounting payments.

Recommended upgrade order:

1. Back up the database and filestore.
2. Deploy the updated `base_hospital_management` and `hospital_accounting_management` modules together.
3. Update Apps List.
4. Upgrade `base_hospital_management`.
5. Install or upgrade `hospital_accounting_management` immediately afterward.
6. Validate existing invoice links, OPD/IPD/Lab invoice creation, payment registration, and patient balances.

## Validation completed

- Python source syntax validated.
- XML files validated for well-formedness.
- Manifest data/demo file references validated.
- Base-module inherited-view XPath targets validated.
- Confirmed no direct accounting-model references or legacy billing symbols remain in `base_hospital_management` Python/XML code.
