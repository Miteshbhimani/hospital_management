# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PatientLabTest(models.Model):
    _inherit = 'patient.lab.test'

    invoice_id = fields.Many2one(
        'account.move', string='Invoice', copy=False,
        domain=[('move_type', '=', 'out_invoice')],
    )
    invoiced = fields.Boolean(string='Invoiced', copy=False)
    invoice_count = fields.Integer(
        string='Invoice Count', compute='_compute_invoice_count',
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

    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = 1 if record.invoice_id else 0

    def _prepare_lab_invoice_lines(self):
        self.ensure_one()
        service = self.env['hospital.accounting.service']
        lines = []
        if self.result_ids:
            for result in self.result_ids:
                test = result.test_id
                lines.append(service._prepare_invoice_line(
                    product=test.product_id,
                    name=test.name,
                    quantity=1.0,
                    price_unit=result.price or test.price or 0.0,
                    taxes=result.tax_ids or test.tax_ids,
                    source_model=result._name,
                    source_id=result.id,
                    service_type=test.service_type or 'lab',
                ))
        else:
            for test in self.test_ids:
                lines.append(service._prepare_invoice_line(
                    product=test.product_id,
                    name=test.name,
                    quantity=1.0,
                    price_unit=test.price or 0.0,
                    taxes=test.tax_ids,
                    source_model=self._name,
                    source_id=self.id,
                    service_type=test.service_type or 'lab',
                ))
        return lines

    def _create_medicine_sale_order(self):
        self.ensure_one()
        if not self.medicine_ids or self.sold:
            return False
        order_lines = []
        for medicine in self.medicine_ids:
            product = medicine.medicine_id.product_variant_id
            order_lines.append((0, 0, {
                'product_id': product.id,
                'product_uom_qty': medicine.quantity,
                'price_unit': medicine.price or product.lst_price,
            }))
        sale_order = self.env['sale.order'].sudo().create({
            'partner_id': self.patient_id.id,
            'date_order': fields.Datetime.now(),
            'client_order_ref': self.test_id.name,
            'order_line': order_lines,
        })
        self.write({'sold': True, 'order': sale_order.id})
        return sale_order

    def create_invoice(self, rec_id=False):
        records = self.browse(rec_id) if rec_id else self
        service = self.env['hospital.accounting.service']
        for record in records:
            if record.invoice_id and record.invoice_id.state != 'cancel':
                raise UserError(_('Invoice already exists for this patient lab test.'))
            record._create_medicine_sale_order()
            invoice = service.create_customer_invoice(
                record.patient_id,
                record._prepare_lab_invoice_lines(),
                origin=record.test_id.name,
                ref=record.test_id.name,
                hospital_context={
                    'hospital_patient_id': record.patient_id.id,
                    'hospital_lab_test_id': record.id,
                    'hospital_invoice_type': 'laboratory',
                    'hospital_department': 'laboratory',
                },
            )
            record.write({'invoice_id': invoice.id, 'invoiced': True})
            charge_source = record.result_ids or record.test_ids
            for item in charge_source:
                test = item.test_id if item._name == 'lab.test.result' else item
                self.env['hms.charge'].sudo().create({
                    'patient_id': record.patient_id.id,
                    'charge_date': fields.Date.context_today(record),
                    'department_area': 'lab',
                    'product_id': test.product_id.id if getattr(test, 'product_id', False) else False,
                    'description': test.name,
                    'quantity': 1.0,
                    'unit_price': (item.price if item._name == 'lab.test.result' else test.price) or 0.0,
                    'payer_type': 'patient',
                    'source_model': record._name,
                    'source_record_id': record.id,
                    'lab_test_id': record.id,
                    'invoice_id': invoice.id,
                    'state': 'invoiced',
                })
        return True

    def action_create_invoice(self):
        self.create_invoice()
        return self.action_view_invoice()

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
