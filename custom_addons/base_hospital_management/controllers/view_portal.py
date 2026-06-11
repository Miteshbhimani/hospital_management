# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request


class ViewPortal(http.Controller):
    """Secure patient portal views for logged-in patients.

    Medical records are fetched with sudo only after constraining every query to
    the current user's partner. This keeps portal UX functional without giving a
    portal user unrestricted model access.
    """

    def _portal_partner(self):
        """Return the logged-in portal/internal user's patient partner."""
        if request.env.user._is_public():
            return False
        return request.env.user.partner_id

    def _attachment_id(self, res_model, res_id):
        """Fetch one related attachment without raw SQL."""
        attachment = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', res_model),
            ('res_id', '=', res_id),
        ], limit=1, order='id desc')
        return attachment.id if attachment else False

    @http.route('/my/vaccinations', type='http', auth='user', website=True)
    def portal_my_vaccine(self, **kw):
        """Render vaccination details only for the logged-in patient."""
        partner = self._portal_partner()
        if not partner:
            return request.redirect('/web/login')

        v_list = []
        vaccinations = request.env['hospital.vaccination'].sudo().search([
            ('patient_id', '=', partner.id),
        ], order='vaccine_date desc, id desc')
        for rec in vaccinations:
            v_list.append({
                'id': rec.id,
                'name': rec.name,
                'vaccine_date': rec.vaccine_date,
                'dose': rec.dose,
                'vaccine_product_id': rec.vaccine_product_id.name,
                'vaccine_price': rec.vaccine_price,
                'attachment_id': self._attachment_id('hospital.vaccination', rec.id),
            })
        return request.render('base_hospital_management.portal_my_vaccines', {
            'vaccinations': v_list,
            'page_name': 'vaccination',
        })

    @http.route(['/my/tests'], type='http', auth='user', website=True)
    def portal_my_tests(self, **kw):
        """Render lab tests only for the logged-in patient."""
        partner = self._portal_partner()
        if not partner:
            return request.redirect('/web/login')

        tests_list = []
        lab_tests = request.env['patient.lab.test'].sudo().search([
            ('patient_id', '=', partner.id),
        ], order='date desc, id desc')
        for rec in lab_tests:
            tests_list.append({
                'id': rec.id,
                'name': rec.test_id.name,
                'date': rec.date,
            })
        return request.render('base_hospital_management.portal_my_tests', {
            'tests': tests_list,
            'page_name': 'lab_test',
        })

    @http.route('/my/tests/<int:test_id>', type='http', auth='user', website=True)
    def tests_view(self, test_id):
        """Render test results after verifying patient ownership."""
        partner = self._portal_partner()
        if not partner:
            return request.redirect('/web/login')

        all_test = request.env['patient.lab.test'].sudo().search([
            ('id', '=', test_id),
            ('patient_id', '=', partner.id),
        ], limit=1)
        if not all_test:
            return request.not_found()

        result_list = []
        for rec in all_test.result_ids.sudo():
            result_list.append({
                'id': rec.id,
                'name': rec.test_id.name,
                'result': rec.result,
                'price': rec.price,
                'attachment_id': self._attachment_id('lab.test.result', rec.id),
            })
        return request.render('base_hospital_management.portal_my_tests_results', {
            'all_test_id': all_test.id,
            'results': result_list,
            'page_name': 'test_results',
        })

    @http.route('/my/op', type='http', auth='user', website=True)
    def portal_my_op(self, **kw):
        """Render OPD visits only for the logged-in patient."""
        partner = self._portal_partner()
        if not partner:
            return request.redirect('/web/login')

        op = request.env['hospital.outpatient'].sudo().search_read(
            [('patient_id', '=', partner.id)],
            ['op_reference', 'op_date', 'doctor_id', 'slot', 'prescription_ids'],
            order='op_date desc, id desc'
        )
        for record in op:
            hours = int(record.get('slot') or 0)
            minutes = int(((record.get('slot') or 0) - hours) * 60)
            record['slot'] = '{:02d}:{:02d}'.format(hours, minutes)
        return request.render('base_hospital_management.portal_my_op', {
            'op': op,
            'page_name': 'op',
        })
