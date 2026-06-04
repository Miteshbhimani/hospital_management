# -*- coding: utf-8 -*-
"""Consent records for privacy-safe healthcare workflows."""
from odoo import api, fields, models


class HospitalConsent(models.Model):
    """Patient consent lifecycle for treatment, data sharing and AI assistance."""
    _name = 'hospital.consent'
    _description = 'Hospital Consent Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Consent No.', required=True, readonly=True, copy=False, default='New')
    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, tracking=True,
        domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])]
    )
    consent_type = fields.Selection([
        ('treatment', 'Treatment Consent'),
        ('surgery', 'Surgery / Procedure Consent'),
        ('data_sharing', 'Data Sharing Consent'),
        ('insurance', 'Insurance / TPA Consent'),
        ('abdm', 'ABDM / ABHA Consent'),
        ('ai_assist', 'AI Assistance Consent'),
        ('telemedicine', 'Telemedicine Consent'),
        ('marketing', 'Patient Engagement / Marketing Consent'),
    ], string='Consent Type', required=True, tracking=True)
    date = fields.Datetime(string='Consent Date', default=fields.Datetime.now, required=True, tracking=True)
    valid_until = fields.Date(string='Valid Until')
    summary = fields.Text(string='Consent Summary', required=True)
    allowed_data_scope = fields.Text(string='Allowed Data Scope')
    purpose = fields.Text(string='Purpose')
    signed_by = fields.Char(string='Signed By')
    witness = fields.Char(string='Witness')
    attachment_id = fields.Many2one('ir.attachment', string='Signed Document')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
        ('revoked', 'Revoked'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', tracking=True)
    revoked_reason = fields.Text(string='Revocation Reason')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.consent') or 'New'
        return super().create(vals_list)

    def action_sign(self):
        self.write({'state': 'signed', 'date': fields.Datetime.now()})

    def action_revoke(self):
        self.write({'state': 'revoked'})

    def action_expire(self):
        self.write({'state': 'expired'})
