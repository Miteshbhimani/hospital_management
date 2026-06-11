# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HospitalAccountingService(models.AbstractModel):
    _name = 'hospital.accounting.service'
    _description = 'Hospital Accounting Service Helpers'

    @api.model
    def _get_sale_journal(self, company=None):
        company = company or self.env.company
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', company.id)
        ], limit=1)
        if not journal:
            raise UserError(_('Please configure at least one Sales Journal for company %s.') % company.display_name)
        return journal

    @api.model
    def _prepare_invoice_line(self, product=None, name=None, quantity=1.0,
                              price_unit=0.0, taxes=None, source_model=False,
                              source_id=False, service_type='other'):
        vals = {
            'name': name or (product.display_name if product else _('Hospital Service')),
            'quantity': quantity or 1.0,
            'price_unit': price_unit or 0.0,
            'hospital_service_type': service_type,
        }
        if product:
            vals['product_id'] = product.id
            if not price_unit:
                vals['price_unit'] = product.lst_price
            if product.taxes_id:
                vals['tax_ids'] = [(6, 0, product.taxes_id.ids)]
        if taxes:
            vals['tax_ids'] = [(6, 0, taxes.ids)]
        if source_model:
            vals['hospital_source_model'] = source_model
        if source_id:
            vals['hospital_source_id'] = source_id
        return (0, 0, vals)

    @api.model
    def create_customer_invoice(self, partner, lines, origin=None, ref=None,
                                invoice_date=None, hospital_context=None,
                                journal=None):
        if not partner:
            raise UserError(_('A patient/customer is required before creating an invoice.'))
        if not lines:
            raise UserError(_('There are no billable lines to invoice.'))
        company = self.env.company
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': invoice_date or fields.Date.context_today(self),
            'date': invoice_date or fields.Date.context_today(self),
            'journal_id': (journal or self._get_sale_journal(company)).id,
            'invoice_origin': origin,
            'ref': ref or origin,
            'invoice_line_ids': lines,
        }
        if hospital_context:
            invoice_vals.update(hospital_context)
        return self.env['account.move'].sudo().create(invoice_vals)

    @api.model
    def create_charge_capture_from_invoice(self, invoice, patient=None,
                                           department_area='other', doctor=None,
                                           outpatient=None, inpatient=None,
                                           lab_test=None, payer_type='patient'):
        """Create hms.charge audit rows from invoice lines without duplicating existing rows.

        This is intentionally separated from ``create_customer_invoice`` so charge-origin
        workflows such as hms.charge.action_create_invoice do not recursively create
        duplicate charge rows.
        """
        if not invoice:
            return self.env['hms.charge']
        patient = patient or invoice.hospital_patient_id or invoice.partner_id
        if not patient:
            return self.env['hms.charge']
        doctor = doctor or invoice.hospital_doctor_id
        outpatient = outpatient or invoice.hospital_outpatient_id
        inpatient = inpatient or invoice.hospital_inpatient_id
        lab_test = lab_test or invoice.hospital_lab_test_id
        charge_model = self.env['hms.charge'].sudo()
        created = charge_model.browse()
        for line in invoice.invoice_line_ids.filtered(lambda l: not l.display_type and (l.quantity or l.price_unit)):
            source_model = line.hospital_source_model or invoice._name
            source_id = line.hospital_source_id or invoice.id
            existing = charge_model.search([
                ('invoice_id', '=', invoice.id),
                ('source_model', '=', source_model),
                ('source_record_id', '=', source_id),
                ('description', '=', line.name or invoice.name or invoice.ref),
            ], limit=1)
            if existing:
                continue
            created |= charge_model.create({
                'patient_id': patient.id,
                'charge_date': invoice.invoice_date or fields.Date.context_today(self),
                'department_area': department_area or 'other',
                'doctor_id': doctor.id if doctor else False,
                'product_id': line.product_id.id if line.product_id else False,
                'description': line.name or invoice.name or invoice.ref or _('Hospital Service'),
                'quantity': line.quantity or 1.0,
                'unit_price': line.price_unit or 0.0,
                'payer_type': payer_type or 'patient',
                'source_model': source_model,
                'source_record_id': source_id,
                'outpatient_id': outpatient.id if outpatient else False,
                'inpatient_id': inpatient.id if inpatient else False,
                'lab_test_id': lab_test.id if lab_test else False,
                'invoice_id': invoice.id,
                'company_id': invoice.company_id.id,
                'currency_id': invoice.currency_id.id,
                'state': 'invoiced',
            })
        return created
