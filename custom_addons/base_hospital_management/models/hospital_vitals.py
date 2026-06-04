# -*- coding: utf-8 -*-
"""Vitals and lightweight EMR observation capture."""
from odoo import api, fields, models


class HospitalVitals(models.Model):
    """Structured vitals charting with abnormal flagging."""
    _name = 'hospital.vitals'
    _description = 'Hospital Vitals / EMR Observation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'recorded_at desc'

    name = fields.Char(string='Observation No.', required=True, readonly=True, copy=False, default='New')
    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, tracking=True,
        domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])]
    )
    outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Visit')
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')
    recorded_by_id = fields.Many2one('res.users', string='Recorded By', default=lambda self: self.env.user, readonly=True)
    recorded_at = fields.Datetime(string='Recorded At', default=fields.Datetime.now, required=True, tracking=True)
    temperature_c = fields.Float(string='Temperature (°C)')
    pulse_rate = fields.Integer(string='Pulse / min')
    respiratory_rate = fields.Integer(string='Respiratory Rate / min')
    systolic_bp = fields.Integer(string='Systolic BP')
    diastolic_bp = fields.Integer(string='Diastolic BP')
    spo2 = fields.Integer(string='SpO2 %')
    height_cm = fields.Float(string='Height (cm)')
    weight_kg = fields.Float(string='Weight (kg)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    pain_score = fields.Selection([(str(i), str(i)) for i in range(0, 11)], string='Pain Score')
    triage_category = fields.Selection([
        ('green', 'Green - Stable'),
        ('yellow', 'Yellow - Urgent'),
        ('orange', 'Orange - Very Urgent'),
        ('red', 'Red - Critical'),
    ], string='Triage Category')
    notes = fields.Text(string='Clinical Notes')
    abnormal = fields.Boolean(string='Abnormal Vitals', compute='_compute_abnormal', store=True)
    abnormal_reason = fields.Char(string='Abnormal Reason', compute='_compute_abnormal', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.vitals') or 'New'
        return super().create(vals_list)

    @api.depends('height_cm', 'weight_kg')
    def _compute_bmi(self):
        for rec in self:
            if rec.height_cm and rec.weight_kg:
                rec.bmi = rec.weight_kg / ((rec.height_cm / 100) ** 2)
            else:
                rec.bmi = 0.0

    @api.depends('temperature_c', 'pulse_rate', 'respiratory_rate', 'systolic_bp', 'diastolic_bp', 'spo2', 'triage_category')
    def _compute_abnormal(self):
        for rec in self:
            reasons = []
            if rec.temperature_c and (rec.temperature_c < 35.0 or rec.temperature_c >= 38.0):
                reasons.append('temperature')
            if rec.pulse_rate and (rec.pulse_rate < 50 or rec.pulse_rate > 120):
                reasons.append('pulse')
            if rec.respiratory_rate and (rec.respiratory_rate < 10 or rec.respiratory_rate > 24):
                reasons.append('respiration')
            if rec.systolic_bp and (rec.systolic_bp < 90 or rec.systolic_bp > 180):
                reasons.append('systolic BP')
            if rec.diastolic_bp and rec.diastolic_bp > 110:
                reasons.append('diastolic BP')
            if rec.spo2 and rec.spo2 < 94:
                reasons.append('SpO2')
            if rec.triage_category in ('orange', 'red'):
                reasons.append('triage')
            rec.abnormal = bool(reasons)
            rec.abnormal_reason = ', '.join(reasons)
