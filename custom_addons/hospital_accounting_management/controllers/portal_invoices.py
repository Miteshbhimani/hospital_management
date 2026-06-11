# -*- coding: utf-8 -*-
"""Hospital invoice portal pages for patient payment visibility."""

from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http


class HospitalAccountingPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        patient = request.env.user.partner_id
        if 'hospital_invoice_count' in counters:
            values['hospital_invoice_count'] = request.env['account.move'].sudo().search_count([
                ('hospital_patient_id', '=', patient.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '!=', 'cancel'),
            ])
        return values

    @http.route('/my/hospital/invoices', type='http', auth='user', website=True)
    def portal_my_hospital_invoices(self, **kwargs):
        patient = request.env.user.partner_id
        invoices = request.env['account.move'].sudo().search([
            ('hospital_patient_id', '=', patient.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '!=', 'cancel'),
        ], order='invoice_date desc, id desc')
        values = {
            'hospital_invoices': [{
                'name': invoice.name or invoice.ref,
                'date': invoice.invoice_date,
                'type': invoice.hospital_invoice_type,
                'department': invoice.hospital_department,
                'amount_total': invoice.amount_total,
                'amount_residual': invoice.amount_residual,
                'payment_state': invoice.payment_state,
                'currency': invoice.currency_id.symbol,
                'url': invoice.get_portal_url() if hasattr(invoice, 'get_portal_url') else '/my/invoices/%s' % invoice.id,
            } for invoice in invoices],
            'page_name': 'hospital_invoices',
        }
        return request.render('hospital_accounting_management.portal_my_hospital_invoices', values)
