# HMS Enterprise Stabilization Implementation Summary

## Version
`base_hospital_management` upgraded to `18.0.1.1.0`.

## Implemented

### 1. OPD Billing Bug Fix
- Fixed invalid `sale.order.line` field `order` to `order_id`.
- Corrected OPD medicine sale order line to use the `product.product` variant from the selected medicine template.
- Prevented empty OPD medicine sale order creation when no OPD/prescription exists.
- Prevented repeated consultation invoice generation inside the prescription-line loop.

### 2. Laboratory Report Bug Fix
- Fixed `rec.test_id.test` to `rec.test_id.name` in lab result PDF data.
- Fixed medicine computation in `patient.lab.test` to use `record.test_ids` instead of `self.test_ids`.

### 3. Portal Security Hardening
- Converted patient medical portal routes from public access to authenticated user access.
- Added patient ownership checks for vaccinations, lab tests, lab test result detail pages and OPD records.
- Replaced raw SQL attachment lookup with safe ORM-based `ir.attachment` searches.
- Prevented cross-patient lab result access through `/my/tests/<id>`.

### 4. Patient Booking Security Hardening
- Converted patient booking submit and doctor-fetch routes to authenticated user access.
- Restored CSRF protection on the booking form.
- Added CSRF token to the website booking form.
- Validated doctor allocation, booking date, confirmed state and slot availability before OPD creation.
- Prevented duplicate same-day OPD booking for the same patient and doctor allocation.

### 5. AI / Rule Suggestion Governance
- Added `hospital.ai.suggestion` model.
- Added human-review workflow: Draft → Pending Review → Accepted / Accepted With Edits / Rejected.
- Added governed disclaimer: `AI-generated, doctor/staff approval required.`
- Added rule-based operational suggestion generation without external AI calls.
- Added Management & AI Dashboard client action and menu.
- Added AI / Rule Suggestions menu, list, form and search views.
- Added role-based access rights for manager, compliance officer, doctor and operational roles.

### 6. Central Charge Capture Foundation
- Added `hms.charge` model for enterprise billing modernization.
- Added Charge Capture menu under Billing.
- Added charge-to-invoice bridge using standard Odoo `account.move` invoices.
- Integrated OPD consultation invoice creation through `hms.charge`.
- Added lab charge records for lab result invoice lines.

### 7. Packaging Cleanup Readiness
- Added explicit dependencies for `portal`, `mail`, and `account`.
- Added dashboard assets for the Management & AI Dashboard.
- Removed duplicate booking success template entry from manifest.

## Remaining Roadmap Items
The full enterprise roadmap still requires deeper phase implementation after this stabilization layer:
- Independent module split (`hms_base`, `hms_patient`, `hms_emr`, etc.).
- Structured EMR/SOAP/diagnosis/problem-list model.
- Full insurance claim lifecycle.
- Radiology/RIS/PACS workflow.
- Pharmacy dispensing and batch/expiry workflow.
- Telemedicine module.
- FHIR/HL7 interoperability modules.
- IoMT/device observation pipeline.
- Multi-hospital enterprise model.
