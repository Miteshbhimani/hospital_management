# -*- coding: utf-8 -*-
from odoo import fields, models


class HospitalInsurance(models.Model):
    _inherit = 'hospital.insurance'

    partner_id = fields.Many2one('res.partner', string='Insurance Company Partner', domain=[('is_company', '=', True)])
    receivable_account_id = fields.Many2one('account.account', string='Insurance Receivable Account', domain=[('account_type', '=', 'asset_receivable')])
    coverage_percent = fields.Float(string='Default Coverage %', default=0.0)
    claim_journal_id = fields.Many2one('account.journal', string='Claim Journal', domain=[('type', '=', 'sale')])
    active = fields.Boolean(default=True)
