# -*- coding: utf-8 -*-
from odoo import fields, models


class PatientRoom(models.Model):
    _inherit = 'patient.room'

    product_id = fields.Many2one('product.product', string='Accounting Product', domain=[('sale_ok', '=', True)])
