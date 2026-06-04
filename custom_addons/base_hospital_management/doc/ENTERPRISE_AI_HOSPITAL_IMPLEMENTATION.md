# Enterprise AI Hospital ERP Increment

## Baseline module analysis

The uploaded add-on is an Odoo 18 hospital management module. It already includes patient registration, OPD/IPD records, doctor allocation and slots, lab tests, pharmacy sale workflow, blood bank, infrastructure masters, patient portal pages, QWeb reports, security groups, and OWL dashboard actions for reception, doctor, laboratory, and pharmacy users.

## Implemented increment

This increment extends the module toward the master ERP prompt while preserving the existing module structure.

### Backend models

- `hospital.appointment`: appointment booking, walk-in queue, token generation, priority/emergency queue, check-in, consultation start, done, no-show and cancellation state handling.
- `hospital.vitals`: structured EMR vitals charting with BMI calculation, triage category and abnormal vital detection.
- `hospital.consent`: patient consent lifecycle for treatment, surgery/procedure, data sharing, ABDM/ABHA, AI assistance, telemedicine and marketing consent.
- `hospital.emergency.case`: emergency registration, triage category, medico-legal flag, emergency clinician assignment and treatment/discharge workflow.
- `hospital.ai.suggestion`: governed AI/rule suggestion log with prompt, output, related record, mandatory human approval, accept/edit/reject states, reviewer and timestamp.
- `res.partner` extension: ABHA/health ID, acquisition source, patient category, emergency contact, allergies, medical history, family history, current medication, risk alerts and links to appointments, vitals, consent and AI suggestions.

### OWL UI

- New `Management & AI Dashboard` client action registered as `hospital_management_dashboard_tags`.
- Dashboard KPI cards for patients, appointments, OPD, IPD, bed occupancy, pending labs, low-stock medicines, active emergency cases and pending AI suggestions.
- Safe suggestion generation button creates auditable operational suggestions without calling an external LLM.
- Latest AI/rule suggestions table opens the review form.

### Security

- New role groups: Compliance Officer, Billing Executive, Insurance / TPA Executive.
- Access rules added for appointment, vitals, consent, emergency and AI governance models.

### Menus and views

New Enterprise ERP menu includes:

- Management & AI Dashboard
- Appointment & Queue
- Vitals / EMR
- Consent Management
- Emergency Triage
- AI Governance Log

### Human approval guardrail

Every AI suggestion record stores the fixed disclaimer: `AI-generated, doctor/staff approval required`. Suggestions cannot be considered complete until a staff user accepts, edits or rejects them.
