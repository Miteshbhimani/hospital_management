# -*- coding: utf-8 -*-
"""Emergency and triage workflow."""
from odoo import api, fields, models, _


class HospitalEmergencyCase(models.Model):
    """Emergency registration, triage and IPD conversion readiness."""
    _name = 'hospital.emergency.case'
    _description = 'Hospital Emergency Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'arrival_time desc'

    name = fields.Char(string='Emergency Case No.', required=True, readonly=True, copy=False, default='New')
    patient_id = fields.Many2one(
        'res.partner', string='Patient', tracking=True,
        domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])]
    )
    patient_name = fields.Char(string='Unregistered Patient Name')
    arrival_time = fields.Datetime(string='Arrival Time', default=fields.Datetime.now, required=True, tracking=True)
    triage_category = fields.Selection([
        ('green', 'Green - Stable'),
        ('yellow', 'Yellow - Urgent'),
        ('orange', 'Orange - Very Urgent'),
        ('red', 'Red - Critical'),
    ], string='Triage Category', default='yellow', required=True, tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Emergency Doctor', domain=[('job_id.name', '=', 'Doctor')])
    nurse_id = fields.Many2one('hr.employee', string='Nurse', domain=[('job_id.name', '=', 'Nurse')])
    medico_legal_case = fields.Boolean(string='Medico-Legal Case')
    arrival_mode = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('ambulance', 'Ambulance'),
        ('referral', 'Referral'),
        ('police', 'Police'),
    ], string='Arrival Mode', default='walk_in')
    presenting_complaint = fields.Text(string='Presenting Complaint', required=True)
    initial_assessment = fields.Text(string='Initial Assessment')
    procedure_notes = fields.Text(string='Emergency Procedure / Medication')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('triaged', 'Triaged'),
        ('under_treatment', 'Under Treatment'),
        ('converted_ipd', 'Converted to IPD'),
        ('discharged', 'Discharged'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.emergency.case') or 'New'
        return super().create(vals_list)

    def action_triage(self):
        self.write({'state': 'triaged'})

    def action_start_treatment(self):
        self.write({'state': 'under_treatment'})

    def action_discharge(self):
        self.write({'state': 'discharged'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_open_inpatient(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('IPD Admission'),
            'res_model': 'hospital.inpatient',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_patient_id': self.patient_id.id},
        }
