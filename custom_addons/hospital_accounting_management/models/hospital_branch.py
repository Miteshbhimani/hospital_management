# -*- coding: utf-8 -*-
"""Branch master used by hospital finance reporting."""

from odoo import fields, models


class HospitalBranch(models.Model):
    _name = 'hospital.branch'
    _description = 'Hospital Branch'
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char(index=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Branch Contact')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        ('hospital_branch_code_company_uniq', 'unique(code, company_id)', 'The branch code must be unique per company.'),
    ]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    primary_branch_id = fields.Many2one('hospital.branch', string='Hospital Branch', index=True)
