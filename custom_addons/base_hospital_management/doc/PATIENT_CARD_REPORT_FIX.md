# Patient Card Report Stabilization

## Fixed issues

- Replaced the undersized 30 x 55 mm report format with a standard 86 x 54 mm patient ID card format.
- Rebuilt the report as a stable two-sided card so identity, contact, company, and barcode data no longer split or clip across unintended pages.
- Added reliable patient-photo rendering through Odoo's `image_data_uri()` helper.
- Added a patient-initials placeholder when no photo is available, avoiding broken-image icons.
- Replaced absolute pixel positioning and Bootstrap containers with wkhtmltopdf-compatible table layouts and millimetre sizing.
- Generates barcodes in memory rather than writing a shared `code.png` file.
- Uses `env.company` instead of an invalid company search domain.
- Keeps the patient card paper format from becoming the global default report format.

No patient workflow, field, access right, or unrelated report behavior was changed.
