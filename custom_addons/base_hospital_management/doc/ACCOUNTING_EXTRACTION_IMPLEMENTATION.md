# Accounting Extraction Implementation

This update removes direct native-accounting model logic from `base_hospital_management`.

Removed from base:

- Direct `account.move`, `account.move.line`, `account.payment.register`, and `account.tax` references.
- Legacy `inpatient.payment` model and ACL rows.
- `hms.charge` charge-capture model/view/sequence/ACL rows.
- OPD/IPD/Lab invoice buttons and invoice smart buttons from base views.
- Patient invoice smart button from the base patient form.

Moved to `hospital_accounting_management`:

- Central `hms.charge` charge-capture model.
- Charge Capture menu, views, sequence, and accounting security.
- OPD consultation invoice creation linked to charge capture.
- Lab invoice creation linked to charge capture.
- Patient invoice portal/accounting actions remain in accounting module.

The base HMS can now hold clinical and operational workflows, while billing, invoices, claims, refunds, tax mapping, payment registration, and financial BI are owned by `hospital_accounting_management`.
