# -*- coding: utf-8 -*-
"""Phase 3 insurance, corporate, package, credit, and claim workflows."""

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalCorporateContract(models.Model):
    _name = 'hospital.corporate.contract'
    _description = 'Hospital Corporate Billing Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Corporate / Employer', required=True, domain=[('is_company', '=', True)])
    code = fields.Char(string='Contract Code', copy=False, index=True)
    valid_from = fields.Date(default=fields.Date.context_today)
    valid_to = fields.Date()
    credit_limit = fields.Monetary(currency_field='currency_id')
    credit_days = fields.Integer(default=30)
    discount_percent = fields.Float(string='Default Discount %')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    package_ids = fields.Many2many('hospital.billing.package', string='Allowed Packages')
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    notes = fields.Text()

    _sql_constraints = [
        ('hospital_corporate_contract_code_uniq', 'unique(code)', 'Corporate contract code must be unique.'),
    ]

    def is_valid_on(self, date=None):
        self.ensure_one()
        date = date or fields.Date.context_today(self)
        if self.valid_from and date < self.valid_from:
            return False
        if self.valid_to and date > self.valid_to:
            return False
        return self.active


class HospitalBillingPackage(models.Model):
    _name = 'hospital.billing.package'
    _description = 'Hospital Billing Package'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True)
    code = fields.Char(copy=False, index=True)
    package_type = fields.Selection([
        ('opd', 'OPD Package'),
        ('ipd', 'IPD Package'),
        ('surgery', 'Surgery Package'),
        ('diagnostic', 'Diagnostic Package'),
        ('corporate', 'Corporate Package'),
        ('other', 'Other'),
    ], default='opd', required=True)
    product_id = fields.Many2one('product.product', string='Package Product')
    line_ids = fields.One2many('hospital.billing.package.line', 'package_id', string='Package Lines')
    package_amount = fields.Monetary(string='Package Amount', compute='_compute_package_amount', store=True, currency_field='currency_id')
    fixed_price = fields.Monetary(string='Fixed Package Price', currency_field='currency_id')
    use_fixed_price = fields.Boolean(string='Use Fixed Price')
    valid_from = fields.Date()
    valid_to = fields.Date()
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    notes = fields.Text()

    @api.depends('line_ids.subtotal', 'fixed_price', 'use_fixed_price')
    def _compute_package_amount(self):
        for package in self:
            package.package_amount = package.fixed_price if package.use_fixed_price else sum(package.line_ids.mapped('subtotal'))

    def _prepare_invoice_lines(self):
        self.ensure_one()
        service = self.env['hospital.accounting.service']
        if self.use_fixed_price or not self.line_ids:
            product = self.product_id or self.env.ref('hospital_accounting_management.product_hospital_package', raise_if_not_found=False)
            return [service._prepare_invoice_line(
                product=product,
                name=_('Package - %s') % self.name,
                quantity=1.0,
                price_unit=self.package_amount,
                source_model=self._name,
                source_id=self.id,
                service_type='other',
            )]
        lines = []
        for line in self.line_ids:
            lines.append(service._prepare_invoice_line(
                product=line.product_id,
                name=line.name or line.product_id.display_name,
                quantity=line.quantity,
                price_unit=line.price_unit,
                source_model=line._name,
                source_id=line.id,
                service_type=line.service_type,
            ))
        return lines


class HospitalBillingPackageLine(models.Model):
    _name = 'hospital.billing.package.line'
    _description = 'Hospital Billing Package Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    package_id = fields.Many2one('hospital.billing.package', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Service / Product')
    name = fields.Char(required=True)
    service_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('room', 'Room/Bed'),
        ('doctor_visit', 'Doctor Visit'),
        ('nursing', 'Nursing'),
        ('surgery', 'Surgery'),
        ('medicine', 'Medicine'),
        ('lab', 'Lab Test'),
        ('radiology', 'Radiology'),
        ('other', 'Other'),
    ], default='other')
    quantity = fields.Float(default=1.0)
    price_unit = fields.Monetary(currency_field='currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='package_id.currency_id', readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.lst_price

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = (line.quantity or 0.0) * (line.price_unit or 0.0)


class HospitalInsuranceClaim(models.Model):
    _name = 'hospital.insurance.claim'
    _description = 'Hospital Insurance / TPA Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'claim_date desc, id desc'

    name = fields.Char(string='Claim No.', default='New', readonly=True, copy=False, index=True)
    claim_date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, index=True,
                                 domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])], tracking=True)
    outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Record')
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')
    invoice_id = fields.Many2one('account.move', string='Hospital Invoice', domain=[('move_type', '=', 'out_invoice')])
    insurance_provider_id = fields.Many2one('hospital.insurance', string='Insurance / TPA Provider', required=True, tracking=True)
    insurance_partner_id = fields.Many2one('res.partner', related='insurance_provider_id.partner_id', store=True, readonly=True)
    claim_type = fields.Selection([
        ('cashless', 'Cashless'),
        ('reimbursement', 'Reimbursement'),
        ('corporate', 'Corporate Insurance'),
    ], default='cashless', required=True)
    policy_number = fields.Char(string='Policy Number')
    member_id = fields.Char(string='Member ID')
    preauth_reference = fields.Char(string='Pre-Authorization Ref.')
    claim_reference = fields.Char(string='TPA Claim Ref.')
    requested_amount = fields.Monetary(currency_field='currency_id', tracking=True)
    approved_amount = fields.Monetary(currency_field='currency_id', tracking=True)
    settled_amount = fields.Monetary(currency_field='currency_id', tracking=True)
    rejected_amount = fields.Monetary(currency_field='currency_id', compute='_compute_rejected_amount', store=True)
    co_pay_percent = fields.Float(string='Co-pay %')
    patient_payable_amount = fields.Monetary(string='Patient Payable', currency_field='currency_id', compute='_compute_split_amounts', store=True)
    insurance_payable_amount = fields.Monetary(string='Insurance Payable', currency_field='currency_id', compute='_compute_split_amounts', store=True)
    deductible_amount = fields.Monetary(currency_field='currency_id')
    preauth_requested_on = fields.Datetime(readonly=True)
    preauth_approved_on = fields.Datetime(readonly=True)
    submitted_on = fields.Datetime(readonly=True)
    approved_on = fields.Datetime(readonly=True)
    settled_on = fields.Datetime(readonly=True)
    rejection_reason = fields.Text()
    settlement_note = fields.Text()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preauth_requested', 'Pre-Auth Requested'),
        ('preauth_approved', 'Pre-Auth Approved'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('settled', 'Settled'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    document_ids = fields.Many2many('ir.attachment', string='Claim Documents')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.insurance.claim') or 'New'
            if vals.get('invoice_id') and not vals.get('requested_amount'):
                invoice = self.env['account.move'].browse(vals['invoice_id'])
                vals['requested_amount'] = invoice.amount_total
        claims = super().create(vals_list)
        for claim in claims:
            claim._sync_invoice_split()
        return claims

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id and self.patient_id.insurance_id:
            self.insurance_provider_id = self.patient_id.insurance_id
            self.policy_number = self.patient_id.unique_id

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            self.patient_id = self.invoice_id.hospital_patient_id or self.invoice_id.partner_id
            self.outpatient_id = self.invoice_id.hospital_outpatient_id
            self.inpatient_id = self.invoice_id.hospital_inpatient_id
            self.requested_amount = self.invoice_id.amount_total
            self.currency_id = self.invoice_id.currency_id

    @api.onchange('insurance_provider_id')
    def _onchange_insurance_provider_id(self):
        if self.insurance_provider_id:
            self.co_pay_percent = max(0.0, 100.0 - (self.insurance_provider_id.coverage_percent or 0.0))

    @api.depends('requested_amount', 'approved_amount', 'co_pay_percent', 'deductible_amount')
    def _compute_split_amounts(self):
        for claim in self:
            base = claim.approved_amount or claim.requested_amount or 0.0
            patient_part = (base * (claim.co_pay_percent or 0.0) / 100.0) + (claim.deductible_amount or 0.0)
            patient_part = min(patient_part, base)
            claim.patient_payable_amount = patient_part
            claim.insurance_payable_amount = max(base - patient_part, 0.0)

    @api.depends('requested_amount', 'approved_amount')
    def _compute_rejected_amount(self):
        for claim in self:
            claim.rejected_amount = max((claim.requested_amount or 0.0) - (claim.approved_amount or 0.0), 0.0)

    def write(self, vals):
        res = super().write(vals)
        if set(vals) & {'invoice_id', 'approved_amount', 'requested_amount', 'co_pay_percent', 'deductible_amount', 'insurance_provider_id'}:
            self._sync_invoice_split()
        return res

    def _sync_invoice_split(self):
        for claim in self.filtered('invoice_id'):
            claim.invoice_id.write({
                'insurance_claim_id': claim.id,
                'insurance_provider_id': claim.insurance_provider_id.id,
                'insurance_claim_reference': claim.claim_reference or claim.preauth_reference or claim.name,
                'patient_amount': claim.patient_payable_amount,
                'insurance_amount': claim.insurance_payable_amount,
                'co_pay_percent': claim.co_pay_percent,
                'billing_mode': 'insurance',
            })

    def action_request_preauth(self):
        self.write({'state': 'preauth_requested', 'preauth_requested_on': fields.Datetime.now()})

    def action_approve_preauth(self):
        for claim in self:
            if not claim.approved_amount:
                claim.approved_amount = claim.requested_amount
        self.write({'state': 'preauth_approved', 'preauth_approved_on': fields.Datetime.now()})

    def action_submit_claim(self):
        self.write({'state': 'submitted', 'submitted_on': fields.Datetime.now()})

    def action_mark_under_review(self):
        self.write({'state': 'under_review'})

    def action_approve_claim(self):
        for claim in self:
            if not claim.approved_amount:
                claim.approved_amount = claim.requested_amount
            claim.write({'state': 'approved', 'approved_on': fields.Datetime.now()})

    def action_settle_claim(self):
        for claim in self:
            if not claim.settled_amount:
                claim.settled_amount = claim.insurance_payable_amount
            claim.write({'state': 'settled', 'settled_on': fields.Datetime.now()})

    def action_reject_claim(self):
        for claim in self:
            if not claim.rejection_reason:
                raise UserError(_('Please enter a rejection reason before rejecting the claim.'))
            claim.state = 'rejected'

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    billing_mode = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('insurance', 'Insurance'),
        ('corporate', 'Corporate'),
        ('package', 'Package'),
    ], string='Hospital Billing Mode', copy=False, default='cash')
    corporate_contract_id = fields.Many2one('hospital.corporate.contract', string='Corporate Contract', copy=False)
    hospital_package_id = fields.Many2one('hospital.billing.package', string='Billing Package', copy=False)
    insurance_claim_id = fields.Many2one('hospital.insurance.claim', string='Insurance Claim', copy=False)
    hospital_radiology_request_id = fields.Many2one('hospital.radiology.request', string='Radiology Request', copy=False, index=True)
    co_pay_percent = fields.Float(string='Co-pay %', copy=False)
    credit_due_date = fields.Date(string='Credit Due Date', copy=False)
    credit_approved_by_id = fields.Many2one('res.users', string='Credit Approved By', copy=False, readonly=True)

    def action_approve_credit_billing(self):
        for move in self:
            if move.billing_mode not in ('credit', 'corporate'):
                move.billing_mode = 'credit'
            if not move.credit_due_date:
                days = move.corporate_contract_id.credit_days if move.corporate_contract_id else 30
                move.credit_due_date = fields.Date.context_today(move) + relativedelta(days=days)
            move.credit_approved_by_id = self.env.user.id

    def action_create_insurance_claim(self):
        self.ensure_one()
        provider = self.insurance_provider_id or self.hospital_patient_id.insurance_id or self.partner_id.insurance_id
        if not provider:
            raise UserError(_('Please set an insurance provider on the invoice or patient before creating a claim.'))
        claim = self.env['hospital.insurance.claim'].create({
            'patient_id': (self.hospital_patient_id or self.partner_id).id,
            'outpatient_id': self.hospital_outpatient_id.id,
            'inpatient_id': self.hospital_inpatient_id.id,
            'invoice_id': self.id,
            'insurance_provider_id': provider.id,
            'requested_amount': self.amount_total,
            'policy_number': (self.hospital_patient_id or self.partner_id).unique_id,
        })
        return {
            'name': _('Insurance Claim'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.insurance.claim',
            'view_mode': 'form',
            'res_id': claim.id,
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'

    corporate_contract_id = fields.Many2one('hospital.corporate.contract', string='Corporate Contract')
    employee_code = fields.Char(string='Employee / Beneficiary Code')


class HospitalOutpatient(models.Model):
    _inherit = 'hospital.outpatient'

    corporate_contract_id = fields.Many2one('hospital.corporate.contract', string='Corporate Contract')
    billing_package_id = fields.Many2one('hospital.billing.package', string='Billing Package', domain=[('package_type', 'in', ('opd', 'corporate', 'diagnostic', 'other'))])
    insurance_claim_ids = fields.One2many('hospital.insurance.claim', 'outpatient_id', string='Insurance Claims')
    insurance_claim_count = fields.Integer(compute='_compute_insurance_claim_count')

    @api.depends('insurance_claim_ids')
    def _compute_insurance_claim_count(self):
        for record in self:
            record.insurance_claim_count = len(record.insurance_claim_ids)

    @api.onchange('patient_id')
    def _onchange_patient_phase3(self):
        if self.patient_id and self.patient_id.corporate_contract_id:
            self.corporate_contract_id = self.patient_id.corporate_contract_id

    def action_view_insurance_claims(self):
        self.ensure_one()
        return {'name': _('Insurance Claims'), 'type': 'ir.actions.act_window', 'res_model': 'hospital.insurance.claim', 'view_mode': 'list,form', 'domain': [('outpatient_id', '=', self.id)]}


class HospitalInpatient(models.Model):
    _inherit = 'hospital.inpatient'

    corporate_contract_id = fields.Many2one('hospital.corporate.contract', string='Corporate Contract')
    billing_package_id = fields.Many2one('hospital.billing.package', string='Billing Package', domain=[('package_type', 'in', ('ipd', 'surgery', 'corporate', 'other'))])
    insurance_claim_ids = fields.One2many('hospital.insurance.claim', 'inpatient_id', string='Insurance Claims')
    insurance_claim_count = fields.Integer(compute='_compute_insurance_claim_count')

    @api.depends('insurance_claim_ids')
    def _compute_insurance_claim_count(self):
        for record in self:
            record.insurance_claim_count = len(record.insurance_claim_ids)

    @api.onchange('patient_id')
    def _onchange_patient_phase3(self):
        if self.patient_id and self.patient_id.corporate_contract_id:
            self.corporate_contract_id = self.patient_id.corporate_contract_id

    def action_view_insurance_claims(self):
        self.ensure_one()
        return {'name': _('Insurance Claims'), 'type': 'ir.actions.act_window', 'res_model': 'hospital.insurance.claim', 'view_mode': 'list,form', 'domain': [('inpatient_id', '=', self.id)]}


class HospitalRadiologyRequest(models.Model):
    _inherit = 'hospital.radiology.request'

    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False, readonly=True)
    invoiced = fields.Boolean(string='Invoiced', copy=False)
    payment_state = fields.Selection(related='invoice_id.payment_state', string='Payment Status', store=True, readonly=True)

    def action_create_invoice(self):
        service = self.env['hospital.accounting.service']
        for request in self:
            if request.invoice_id and request.invoice_id.state != 'cancel':
                raise UserError(_('Invoice already exists for %s.') % request.name)
            product = request.modality_id.product_id.product_variant_id if request.modality_id.product_id else self.env.ref(
                'hospital_accounting_management.product_hospital_radiology', raise_if_not_found=False)
            price_unit = request.estimated_price or (product.lst_price if product else 0.0)
            line = service._prepare_invoice_line(
                product=product,
                name=_('Radiology - %(modality)s - %(body)s') % {
                    'modality': request.modality_id.display_name,
                    'body': request.body_part,
                },
                quantity=1.0,
                price_unit=price_unit,
                source_model=request._name,
                source_id=request.id,
                service_type='radiology',
            )
            invoice = service.create_customer_invoice(
                request.patient_id,
                [line],
                origin=request.name,
                ref=request.accession_number or request.name,
                hospital_context={
                    'hospital_patient_id': request.patient_id.id,
                    'hospital_outpatient_id': request.outpatient_id.id,
                    'hospital_inpatient_id': request.inpatient_id.id,
                    'hospital_radiology_request_id': request.id,
                    'hospital_invoice_type': 'radiology',
                    'hospital_department': 'radiology',
                    'hospital_doctor_id': request.doctor_id.id,
                },
            )
            request.write({'invoice_id': invoice.id, 'invoiced': True})
        return self[:1].action_view_invoice()

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
