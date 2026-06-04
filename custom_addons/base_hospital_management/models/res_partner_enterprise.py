# -*- coding: utf-8 -*-
"""Enterprise patient profile extensions for Hospital Management."""
from odoo import fields, models


class ResPartner(models.Model):
    """Add ERP-grade patient master data required by the roadmap."""
    _inherit = 'res.partner'

    abha_number = fields.Char(
        string='ABHA / Health ID',
        copy=False,
        help='ABHA or national health identifier when captured with patient consent.',
    )
    acquisition_source = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('website', 'Website Enquiry'),
        ('emergency', 'Emergency'),
        ('doctor_referral', 'Doctor Referral'),
        ('insurance_tpa', 'Insurance / TPA Referral'),
        ('corporate', 'Corporate Tie-up'),
        ('camp', 'Health Camp'),
        ('online', 'Online Appointment'),
        ('teleconsultation', 'Teleconsultation'),
        ('follow_up', 'Repeat Follow-up'),
    ], string='Acquisition Source', default='walk_in', tracking=True)
    patient_category = fields.Selection([
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('emergency', 'Emergency'),
        ('corporate', 'Corporate'),
        ('insurance', 'Insurance / TPA'),
        ('camp', 'Health Camp'),
    ], string='Patient Category', default='opd', tracking=True)
    emergency_contact_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')
    emergency_contact_relation = fields.Char(string='Emergency Contact Relation')
    allergy_note = fields.Text(string='Allergies')
    medical_history_note = fields.Text(string='Medical History')
    family_history_note = fields.Text(string='Family History')
    current_medication_note = fields.Text(string='Current Medication')
    risk_alert_note = fields.Text(string='Clinical / Administrative Risk Alerts')
    consent_ids = fields.One2many('hospital.consent', 'patient_id', string='Consent Records')
    vitals_ids = fields.One2many('hospital.vitals', 'patient_id', string='Vitals')
    appointment_ids = fields.One2many('hospital.appointment', 'patient_id', string='Appointments')
