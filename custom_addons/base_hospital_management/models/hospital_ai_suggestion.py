# -*- coding: utf-8 -*-
"""Governed AI/rule-based suggestion log for hospital operations.

This model intentionally stores suggestions as reviewable drafts. It does not
write clinical or financial records automatically; a human user must accept,
edit or reject each suggestion.
"""
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalAiSuggestion(models.Model):
    """Human-reviewed AI/rule suggestion queue."""
    _name = 'hospital.ai.suggestion'
    _description = 'Hospital AI / Rule Suggestion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, severity desc, id desc'

    name = fields.Char(string='Suggestion No.', required=True, readonly=True, copy=False, default='New')
    title = fields.Char(string='Title', required=True, tracking=True)
    source_area = fields.Selection([
        ('operations', 'Operations'),
        ('patient', 'Patient Management'),
        ('appointment', 'Appointment / Queue'),
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('lab', 'Laboratory'),
        ('pharmacy', 'Pharmacy'),
        ('inventory', 'Inventory'),
        ('billing', 'Billing'),
        ('emergency', 'Emergency'),
        ('compliance', 'Compliance'),
    ], string='Area', default='operations', required=True, tracking=True)
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Severity', default='medium', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('edited', 'Accepted With Edits'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending_review', required=True, tracking=True)

    patient_id = fields.Many2one('res.partner', string='Patient')
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment')
    outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Visit')
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')
    lab_test_id = fields.Many2one('patient.lab.test', string='Lab Test')
    emergency_id = fields.Many2one('hospital.emergency.case', string='Emergency Case')

    source_model = fields.Char(string='Source Model', readonly=True)
    source_record_id = fields.Integer(string='Source Record ID', readonly=True)
    prompt_text = fields.Text(string='Input / Rule Context')
    suggestion_text = fields.Text(string='Suggestion', required=True)
    reviewed_text = fields.Text(string='Reviewed / Edited Suggestion')
    disclaimer = fields.Char(
        string='Disclaimer',
        default='AI-generated, doctor/staff approval required.',
        readonly=True,
    )
    reviewed_by = fields.Many2one('res.users', string='Reviewed By', readonly=True)
    reviewed_at = fields.Datetime(string='Reviewed At', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.ai.suggestion') or 'New'
        return super().create(vals_list)

    def action_submit_review(self):
        self.write({'state': 'pending_review'})

    def action_accept(self):
        self.write({
            'state': 'accepted',
            'reviewed_by': self.env.user.id,
            'reviewed_at': fields.Datetime.now(),
            'reviewed_text': False,
        })

    def action_mark_edited(self):
        for rec in self:
            if not rec.reviewed_text:
                raise UserError(_('Add the reviewed/edited suggestion text before marking this suggestion as accepted with edits.'))
        self.write({
            'state': 'edited',
            'reviewed_by': self.env.user.id,
            'reviewed_at': fields.Datetime.now(),
        })

    def action_reject(self):
        self.write({
            'state': 'rejected',
            'reviewed_by': self.env.user.id,
            'reviewed_at': fields.Datetime.now(),
        })

    def action_reset_to_draft(self):
        self.write({
            'state': 'draft',
            'reviewed_by': False,
            'reviewed_at': False,
        })

    def _today_bounds(self):
        tz_name = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        tz = pytz.timezone(tz_name)
        local_now = datetime.now(tz)
        local_today_start = tz.localize(datetime.combine(local_now.date(), time.min))
        local_today_end = local_today_start + timedelta(days=1)
        utc_start = local_today_start.astimezone(pytz.UTC)
        utc_end = local_today_end.astimezone(pytz.UTC)
        return (
            fields.Date.to_string(local_now.date()),
            fields.Datetime.to_string(utc_start),
            fields.Datetime.to_string(utc_end),
        )

    def _safe_count(self, model_name, domain=None):
        if model_name not in self.env:
            return 0
        return self.env[model_name].sudo().search_count(domain or [])

    def _low_stock_medicine_count(self):
        if 'product.template' not in self.env:
            return 0
        medicines = self.env['product.template'].sudo().search([('medicine_ok', '=', True)])
        return len(medicines.filtered(lambda product: product.qty_available <= 5))

    def _bed_occupancy_payload(self):
        total_beds = self._safe_count('hospital.bed', [])
        available_beds = self._safe_count('hospital.bed', [('state', '=', 'avail')])
        occupied = max(total_beds - available_beds, 0)
        occupancy = round((occupied / total_beds) * 100, 2) if total_beds else 0
        return total_beds, available_beds, occupancy

    @api.model
    def get_hospital_ai_dashboard(self):
        """Return management dashboard data consumed by the OWL client action."""
        today, start_dt, end_dt = self._today_bounds()
        total_beds, available_beds, bed_occupancy = self._bed_occupancy_payload()
        latest = self.sudo().search_read(
            [],
            ['name', 'title', 'source_area', 'severity', 'state', 'disclaimer'],
            limit=10,
            order='create_date desc, id desc',
        )
        return {
            'disclaimer': 'AI-generated, doctor/staff approval required.',
            'cards': {
                'patients': self._safe_count('res.partner', [('patient_seq', 'not in', ['New', 'Employee', 'User'])]),
                'appointments_today': self._safe_count('hospital.appointment', [
                    ('appointment_date', '>=', start_dt),
                    ('appointment_date', '<', end_dt),
                    ('state', 'not in', ['cancelled']),
                ]),
                'opd_today': self._safe_count('hospital.outpatient', [('op_date', '=', today), ('state', '!=', 'cancel')]),
                'ipd_admitted': self._safe_count('hospital.inpatient', [('state', '=', 'admit')]),
                'bed_occupancy': bed_occupancy,
                'beds_total': total_beds,
                'beds_available': available_beds,
                'lab_pending': self._safe_count('patient.lab.test', [('state', 'in', ['draft', 'test'])]),
                'pharmacy_low_stock': self._low_stock_medicine_count(),
                'emergency_active': self._safe_count('hospital.emergency.case', [('state', 'in', ['draft', 'triaged', 'under_treatment'])]),
            },
            'ai': {
                'pending': self.sudo().search_count([('state', 'in', ['draft', 'pending_review'])]),
                'accepted': self.sudo().search_count([('state', '=', 'accepted')]),
                'edited': self.sudo().search_count([('state', '=', 'edited')]),
                'rejected': self.sudo().search_count([('state', '=', 'rejected')]),
                'latest': latest,
            },
        }

    def _create_rule_suggestion(self, title, area, severity, suggestion_text, prompt_text=None):
        existing = self.sudo().search([
            ('title', '=', title),
            ('source_area', '=', area),
            ('state', 'in', ['draft', 'pending_review']),
        ], limit=1)
        if existing:
            return False
        self.sudo().create({
            'title': title,
            'source_area': area,
            'severity': severity,
            'prompt_text': prompt_text or _('Rule-based operational monitor'),
            'suggestion_text': suggestion_text,
            'state': 'pending_review',
        })
        return True

    @api.model
    def generate_rule_based_suggestions(self):
        """Generate safe, deterministic suggestions from current HMS data.

        This is deliberately rule-based. It creates review queue items without
        calling any external AI provider and without changing source records.
        """
        created = 0
        lab_pending = self._safe_count('patient.lab.test', [('state', 'in', ['draft', 'test'])])
        if lab_pending:
            created += bool(self._create_rule_suggestion(
                _('Pending laboratory workload'),
                'lab',
                'high' if lab_pending >= 10 else 'medium',
                _('There are %s laboratory tests waiting or in progress. Review sample collection, result entry and validation capacity.') % lab_pending,
            ))

        low_stock_count = self._low_stock_medicine_count()
        if low_stock_count:
            created += bool(self._create_rule_suggestion(
                _('Low-stock pharmacy medicines'),
                'pharmacy',
                'high' if low_stock_count >= 5 else 'medium',
                _('%s medicine product(s) are at or below 5 available units. Review reorder rules, vendor lead time and expiry-safe procurement.') % low_stock_count,
            ))

        active_emergency = self._safe_count('hospital.emergency.case', [('state', 'in', ['draft', 'triaged', 'under_treatment'])])
        if active_emergency:
            created += bool(self._create_rule_suggestion(
                _('Active emergency cases need supervision'),
                'emergency',
                'critical' if active_emergency >= 3 else 'high',
                _('%s emergency case(s) are still open. Review triage, doctor assignment and conversion/discharge status.') % active_emergency,
            ))

        total_beds, available_beds, occupancy = self._bed_occupancy_payload()
        if total_beds and occupancy >= 85:
            created += bool(self._create_rule_suggestion(
                _('High bed occupancy'),
                'ipd',
                'critical' if occupancy >= 95 else 'high',
                _('Current bed occupancy is %s%% with %s available bed(s). Review discharge readiness, transfers and elective admission planning.') % (occupancy, available_beds),
            ))

        return {'created': created}
