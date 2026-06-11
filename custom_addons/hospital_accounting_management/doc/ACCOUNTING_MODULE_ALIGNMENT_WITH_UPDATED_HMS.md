# Accounting Module Alignment With Updated HMS

This module has been aligned with the stabilized HMS package.

Key changes:

- Added ownership of `hms.charge` charge capture.
- Added the `CHG/` sequence inside the accounting module.
- Added charge-capture ACL rows for cashier, accountant, and finance manager groups.
- Re-parented the Billing menu into this module, under the Hospital Management root.
- Fixed the old missing parent menu reference `base_hospital_management.hospital_menu_billing_insurance`.
- OPD invoice creation now creates a charge and then creates the Odoo invoice from that charge.
- Lab invoice creation creates linked charge-capture records after invoice creation.

Upgrade order:

1. Upgrade `base_hospital_management`.
2. Upgrade/install `hospital_accounting_management`.
3. Upgrade `hospital_staff_access_management` if staff groups were changed.
