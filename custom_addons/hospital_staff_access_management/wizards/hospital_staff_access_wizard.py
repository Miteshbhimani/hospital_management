# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HospitalStaffAccessWizard(models.TransientModel):
    _name = "hospital.staff.access.wizard"
    _description = "Hospital Staff User Access Wizard"

    employee_id = fields.Many2one("hr.employee", string="Staff", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", string="Linked User", readonly=True)
    hospital_staff_role = fields.Selection(
        related="employee_id.hospital_staff_role",
        string="Hospital Role",
        readonly=False,
        required=True,
    )
    login = fields.Char(string="Login Email", required=True)
    temporary_password = fields.Char(
        string="Temporary Password",
        help="Optional. When filled, the wizard sets this as the user's password. Leave empty if you want to set/reset the password manually from Settings later.",
    )
    update_existing_user = fields.Boolean(
        string="Link existing user if login already exists",
        default=True,
    )
    group_preview_ids = fields.Many2many("res.groups", string="Groups to Apply", compute="_compute_group_preview_ids")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        employee = self.env["hr.employee"].browse(res.get("employee_id") or self.env.context.get("default_employee_id"))
        if employee:
            res.setdefault("user_id", employee.user_id.id)
            res.setdefault("login", employee.work_email or employee.user_id.login)
            res.setdefault("hospital_staff_role", employee.hospital_staff_role)
        return res

    @api.depends("hospital_staff_role")
    def _compute_group_preview_ids(self):
        for wizard in self:
            groups = self.env["res.groups"]
            internal_group = self.env.ref("base.group_user", raise_if_not_found=False)
            if internal_group:
                groups |= internal_group
            if wizard.hospital_staff_role:
                groups |= wizard.employee_id._hospital_role_group(wizard.hospital_staff_role)
            wizard.group_preview_ids = groups

    def _require_hospital_access_manager(self):
        if self.env.is_superuser():
            return
        if self.env.user.has_group("base.group_system"):
            return
        if self.env.user.has_group("base_hospital_management.base_hospital_management_group_manager"):
            return
        raise AccessError(_("Only Hospital Managers or system administrators can manage hospital staff access."))

    def action_confirm(self):
        self.ensure_one()
        self._require_hospital_access_manager()
        employee = self.employee_id.sudo()
        if not self.hospital_staff_role:
            raise ValidationError(_("Please select the Hospital Role."))
        if not self.login:
            raise ValidationError(_("Please enter the login email."))

        Users = self.env["res.users"].sudo().with_context(no_reset_password=True, create_user_from_employee=True)
        user = employee.user_id
        existing_user = Users.search([("login", "=", self.login)], limit=1)
        if existing_user and existing_user != user:
            if not self.update_existing_user:
                raise UserError(_("A user with login %s already exists. Enable the option to link the existing user.") % self.login)
            user = existing_user

        company = employee.company_id or self.env.company
        if not user:
            user_vals = {
                "name": employee.name,
                "login": self.login,
                "email": self.login,
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "groups_id": [(6, 0, self.group_preview_ids.ids)],
            }
            if self.temporary_password:
                user_vals["password"] = self.temporary_password
            user = Users.create(user_vals)
        else:
            user_vals = {
                "name": employee.name,
                "login": self.login,
                "email": self.login,
                "company_id": company.id,
                "company_ids": [(4, company.id)],
            }
            if self.temporary_password:
                user_vals["password"] = self.temporary_password
            user.write(user_vals)

        employee.write({
            "user_id": user.id,
            "work_email": self.login,
            "hospital_staff_role": self.hospital_staff_role,
        })
        employee._sync_hospital_user_groups(user, self.hospital_staff_role)
        employee.write({"hospital_last_access_sync": fields.Datetime.now()})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Staff access ready"),
                "message": _("User access has been created/updated for %s.") % employee.name,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
