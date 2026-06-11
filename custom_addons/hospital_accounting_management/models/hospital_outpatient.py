# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class HospitalOutpatient(models.Model):
    _inherit = 'hospital.outpatient'

    state = fields.Selection(
        selection_add=[('invoice', 'Invoiced')],
        ondelete={'invoice': 'set default'},
    )
    invoiced = fields.Boolean(default=False, string='Invoiced', copy=False)
    invoice_id = fields.Many2one(
        'account.move', string='Invoice', copy=False,
        domain=[('move_type', '=', 'out_invoice')],
    )
    payment_state = fields.Selection(
        related='invoice_id.payment_state', string='Payment Status',
        store=True, readonly=True,
    )
    amount_total = fields.Monetary(
        related='invoice_id.amount_total', string='Invoice Total',
        currency_field='currency_id', readonly=True,
    )
    amount_residual = fields.Monetary(
        related='invoice_id.amount_residual', string='Outstanding',
        currency_field='currency_id', readonly=True,
    )
    currency_id = fields.Many2one(
        related='invoice_id.currency_id', string='Currency', readonly=True,
    )

    def create_invoice(self):
        for record in self:
            if record.invoice_id and record.invoice_id.state != 'cancel':
                raise UserError(_('Invoice already exists for %s.') % record.display_name)
            doctor = record.doctor_id.doctor_id
            product = doctor.consultation_product_id or self.env.ref(
                'hospital_accounting_management.product_hospital_consultation',
                raise_if_not_found=False,
            )
            charge = self.env['hms.charge'].sudo().create({
                'patient_id': record.patient_id.id,
                'charge_date': fields.Date.context_today(record),
                'department_area': 'opd',
                'doctor_id': doctor.id,
                'product_id': product.id if product else False,
                'description': _('Consultation fee - %s') % (doctor.name or ''),
                'quantity': 1.0,
                'unit_price': doctor.consultancy_charge or (product.lst_price if product else 0.0),
                'payer_type': 'patient',
                'source_model': record._name,
                'source_record_id': record.id,
                'outpatient_id': record.id,
                'state': 'ready',
            })
            charge.action_create_invoice()
            record.write({'invoice_id': charge.invoice_id.id, 'invoiced': True, 'state': 'invoice'})
        return True

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'context': {'create': False},
        }

    def action_register_hospital_payment(self):
        self.ensure_one()
        return {
            'name': _('Register Hospital Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_invoice_id': self.invoice_id.id},
        }
