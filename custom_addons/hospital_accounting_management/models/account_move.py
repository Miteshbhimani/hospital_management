# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    hospital_patient_id = fields.Many2one('res.partner', string='Hospital Patient', index=True, copy=False)
    hospital_outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Record', copy=False, index=True)
    hospital_inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission', copy=False, index=True)
    hospital_lab_test_id = fields.Many2one('patient.lab.test', string='Patient Lab Test', copy=False, index=True)
    hospital_invoice_type = fields.Selection([
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('insurance', 'Insurance Claim'),
        ('advance', 'Advance'),
        ('other', 'Other'),
    ], string='Hospital Invoice Type', copy=False, index=True)
    hospital_department = fields.Selection([
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('surgery', 'Surgery'),
        ('other', 'Other'),
    ], string='Hospital Department', copy=False, index=True)
    hospital_doctor_id = fields.Many2one('hr.employee', string='Doctor', copy=False, index=True)
    insurance_provider_id = fields.Many2one('hospital.insurance', string='Insurance Provider', copy=False, index=True)
    insurance_claim_reference = fields.Char(string='Insurance Claim Reference', copy=False)
    patient_amount = fields.Monetary(string='Patient Portion', currency_field='currency_id', copy=False)
    insurance_amount = fields.Monetary(string='Insurance Portion', currency_field='currency_id', copy=False)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    hospital_source_model = fields.Char(string='Hospital Source Model', copy=False, index=True)
    hospital_source_id = fields.Integer(string='Hospital Source ID', copy=False, index=True)
    hospital_service_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('followup', 'Follow-up'),
        ('procedure', 'Procedure'),
        ('room', 'Room/Bed'),
        ('doctor_visit', 'Doctor Visit'),
        ('nursing', 'Nursing'),
        ('surgery', 'Surgery'),
        ('medicine', 'Medicine'),
        ('lab', 'Lab Test'),
        ('radiology', 'Radiology'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ], string='Hospital Service Type', copy=False, index=True)
