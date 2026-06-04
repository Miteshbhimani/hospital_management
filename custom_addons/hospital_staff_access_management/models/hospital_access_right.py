# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, UserError


class HospitalAccessRight(models.Model):
    _name = "hospital.access.right"
    _description = "Hospital Access Right"
    _auto = False
    _rec_name = "user_name"
    _order = "hospital_role, user_name"

    user_id = fields.Many2one("res.users", string="User", readonly=True)
    user_name = fields.Char(string="User Name", readonly=True)
    login = fields.Char(string="Login", readonly=True)
    active = fields.Boolean(string="Active", readonly=True)
    group_id = fields.Many2one("res.groups", string="Access Group", readonly=True)
    hospital_role = fields.Selection(
        selection=[
            ("doctor", "Doctor"),
            ("nurse", "Nurse"),
            ("receptionist", "Receptionist"),
            ("lab_technician", "Lab Technician"),
            ("pharmacist", "Pharmacist"),
            ("manager", "Hospital Manager"),
        ],
        string="Hospital Access Role",
        readonly=True,
    )
    employee_id = fields.Many2one("hr.employee", string="Linked Staff", readonly=True)
    employee_job_id = fields.Many2one("hr.job", string="Job Position", readonly=True)
    employee_primary_role = fields.Selection(
        selection=[
            ("doctor", "Doctor"),
            ("nurse", "Nurse"),
            ("receptionist", "Receptionist"),
            ("lab_technician", "Lab Technician"),
            ("pharmacist", "Pharmacist"),
            ("manager", "Hospital Manager"),
        ],
        string="Primary Staff Role",
        readonly=True,
    )
    company_id = fields.Many2one("res.company", string="Company", readonly=True)

    _ROLE_GROUP_XMLIDS = [
        (1, "doctor", "base_hospital_management.base_hospital_management_group_doctor"),
        (2, "nurse", "base_hospital_management.base_hospital_management_group_nurse"),
        (3, "receptionist", "base_hospital_management.base_hospital_management_group_receptionist"),
        (4, "lab_technician", "base_hospital_management.base_hospital_management_group_lab_assistant"),
        (5, "pharmacist", "base_hospital_management.base_hospital_management_group_pharmacist"),
        (6, "manager", "base_hospital_management.base_hospital_management_group_manager"),
    ]

    def _require_hospital_access_manager(self):
        if self.env.is_superuser():
            return
        if self.env.user.has_group("base.group_system"):
            return
        if self.env.user.has_group("base_hospital_management.base_hospital_management_group_manager"):
            return
        raise AccessError(_("Only Hospital Managers or system administrators can open hospital access rights."))

    @api.model
    def _role_group_rows_sql(self):
        rows = []
        for sequence, role, xmlid in self._ROLE_GROUP_XMLIDS:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                rows.append("(%s, %s, %s)" % (group.id, self.env.cr.mogrify("%s", [role]).decode(), sequence))
        if not rows:
            # Empty VALUES with the right column types, so the view remains valid
            # even if an upstream installation temporarily misses a group XML ID.
            return "SELECT NULL::integer AS group_id, NULL::varchar AS role, NULL::integer AS role_seq WHERE false"
        return "VALUES %s" % ",".join(rows)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        role_rows = self._role_group_rows_sql()
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH hospital_roles(group_id, role, role_seq) AS (%s),
                employee_match AS (
                    SELECT DISTINCT ON (he.user_id)
                        he.user_id,
                        he.id AS employee_id,
                        he.job_id AS employee_job_id,
                        he.hospital_staff_role AS employee_primary_role,
                        he.company_id AS employee_company_id
                    FROM hr_employee he
                    WHERE he.user_id IS NOT NULL
                    ORDER BY he.user_id, he.active DESC, he.id
                )
                SELECT
                    (u.id * 100 + hr.role_seq) AS id,
                    u.id AS user_id,
                    COALESCE(rp.name, u.login) AS user_name,
                    u.login AS login,
                    u.active AS active,
                    hr.group_id AS group_id,
                    hr.role AS hospital_role,
                    em.employee_id AS employee_id,
                    em.employee_job_id AS employee_job_id,
                    em.employee_primary_role AS employee_primary_role,
                    COALESCE(em.employee_company_id, u.company_id) AS company_id
                FROM res_users u
                    JOIN res_groups_users_rel rel ON rel.uid = u.id
                    JOIN hospital_roles hr ON hr.group_id = rel.gid
                    LEFT JOIN res_partner rp ON rp.id = u.partner_id
                    LEFT JOIN employee_match em ON em.user_id = u.id
            )
        """ % (self._table, role_rows))

    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        self._require_hospital_access_manager()
        return super().search(args, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        self._require_hospital_access_manager()
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def action_open_user(self):
        self.ensure_one()
        self._require_hospital_access_manager()
        if not self.user_id:
            raise UserError(_("No linked Odoo user was found."))
        return {
            "name": _("User Access"),
            "type": "ir.actions.act_window",
            "res_model": "res.users",
            "view_mode": "form",
            "res_id": self.user_id.id,
            "target": "current",
        }

    def action_open_staff(self):
        self.ensure_one()
        self._require_hospital_access_manager()
        if not self.employee_id:
            raise UserError(_("No linked staff record was found for this user."))
        return {
            "name": _("Staff"),
            "type": "ir.actions.act_window",
            "res_model": "hr.employee",
            "view_mode": "form",
            "res_id": self.employee_id.id,
            "target": "current",
        }


    @api.model
    def _cleanup_configuration_access_right_menus(self):
        """Move official Access Rights menus out of Configuration and remove stale duplicates.

        Some earlier package versions placed Access Rights below the Configuration menu.
        Running this method from XML during upgrade keeps the supported top-level menu
        and removes any old duplicate Access Rights nodes that still live under Configuration.
        """
        Menu = self.env["ir.ui.menu"].sudo()
        config_menu = self.env.ref(
            "base_hospital_management.hospital_menu_configuration",
            raise_if_not_found=False,
        )
        hospital_root = self.env.ref(
            "base_hospital_management.hospital_menu_root",
            raise_if_not_found=False,
        )
        manager_group = self.env.ref(
            "base_hospital_management.base_hospital_management_group_manager",
            raise_if_not_found=False,
        )

        official_menu_xmlids = [
            "hospital_staff_access_management.hospital_access_right_menu_root",
            "hospital_staff_access_management.hospital_access_right_menu_all",
            "hospital_staff_access_management.hospital_access_right_menu_doctor",
            "hospital_staff_access_management.hospital_access_right_menu_nurse",
            "hospital_staff_access_management.hospital_access_right_menu_receptionist",
            "hospital_staff_access_management.hospital_access_right_menu_lab",
            "hospital_staff_access_management.hospital_access_right_menu_pharmacist",
            "hospital_staff_access_management.hospital_access_right_menu_manager",
        ]
        official_menus = Menu.browse()
        for xmlid in official_menu_xmlids:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                official_menus |= menu.sudo()

        root_menu = self.env.ref(
            "hospital_staff_access_management.hospital_access_right_menu_root",
            raise_if_not_found=False,
        )
        if root_menu and hospital_root:
            root_menu.sudo().write({"parent_id": hospital_root.id})

        if manager_group and official_menus:
            official_menus.write({"groups_id": [(6, 0, [manager_group.id])]})

        if config_menu:
            stale_menus = Menu.search([
                ("id", "child_of", config_menu.id),
                ("name", "ilike", "Access Rights"),
            ])
            (stale_menus - official_menus).unlink()
        return True
