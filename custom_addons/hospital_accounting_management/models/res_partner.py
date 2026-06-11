# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hospital_invoice_ids = fields.One2many('account.move', 'hospital_patient_id', string='Hospital Invoices')
    hospital_invoice_count = fields.Integer(compute='_compute_hospital_financials', string='Hospital Invoice Count')
    hospital_total_invoiced = fields.Monetary(compute='_compute_hospital_financials', currency_field='currency_id', string='Hospital Total Invoiced')
    hospital_total_residual = fields.Monetary(compute='_compute_hospital_financials', currency_field='currency_id', string='Hospital Outstanding')
    hospital_total_paid = fields.Monetary(compute='_compute_hospital_financials', currency_field='currency_id', string='Hospital Paid')
    insurance_policy_number = fields.Char(string='Insurance Policy Number')
    insurance_coverage_percent = fields.Float(string='Insurance Coverage %', default=0.0)
    insurance_partner_id = fields.Many2one('res.partner', string='Insurance Billing Partner', domain=[('is_company', '=', True)])

    def _compute_hospital_financials(self):
        for partner in self:
            invoices = self.env['account.move'].sudo().search([
                ('move_type', '=', 'out_invoice'),
                ('hospital_patient_id', '=', partner.id),
                ('state', '!=', 'cancel'),
            ])
            partner.hospital_invoice_count = len(invoices)
            partner.hospital_total_invoiced = sum(invoices.mapped('amount_total'))
            partner.hospital_total_residual = sum(invoices.mapped('amount_residual'))
            partner.hospital_total_paid = partner.hospital_total_invoiced - partner.hospital_total_residual

    def action_view_hospital_invoices(self):
        self.ensure_one()
        return {
            'name': 'Hospital Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('hospital_patient_id', '=', self.id), ('move_type', '=', 'out_invoice')],
            'context': {'default_move_type': 'out_invoice', 'default_partner_id': self.id, 'default_hospital_patient_id': self.id},
        }
