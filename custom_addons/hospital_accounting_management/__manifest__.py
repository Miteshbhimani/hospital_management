{'application': False,
 'author': 'Miteshbhimani',
 'auto_install': False,
 'category': 'Accounting/Accounting',
 'data': ['security/hospital_accounting_security.xml',
          'security/ir.model.access.csv',
          'data/hospital_accounting_data.xml',
          'data/hospital_phase3_data.xml',
          'views/account_move_views.xml',
          'views/account_move_phase3_views.xml',
          'views/radiology_accounting_views.xml',
          'views/res_partner_views.xml',
          'views/hospital_insurance_views.xml',
          'views/hospital_service_mapping_views.xml',
          'views/hospital_outpatient_views.xml',
          'views/hospital_inpatient_views.xml',
          'views/patient_lab_test_views.xml',
          'wizards/hospital_payment_register_views.xml',
          'wizards/hospital_advance_refund_wizard_views.xml',
          'views/hospital_accounting_dashboard_views.xml',
          'views/hospital_advance_refund_views.xml',
          'views/hospital_accounting_menu.xml',
          'views/hospital_billing_views.xml',
          'views/hospital_phase3_finance_views.xml',
          'report/hospital_patient_ledger_report.xml',
          'views/hospital_portal_payment_templates.xml',
          'data/hospital_phase6_sequences.xml',
          'views/hospital_branch_views.xml',
          'views/hospital_phase6_finance_views.xml'],
 'depends': ['base_hospital_management', 'account', 'sale_management', 'stock'],
 'description': '\n'
                'Hospital Accounting Management\n'
                '==============================\n'
                'Separate accounting integration module for base_hospital_management.\n'
                'All invoice, payment, tax, receivable, and hospital financial reporting logic\n'
                'is isolated in this module and uses native Odoo Accounting models.\n'
                '    ',
 'assets': {
          'web.assets_backend': [
              'hospital_accounting_management/static/src/css/hospital_accounting_dashboard.css',
          ],
      },
 'installable': True,
 'license': 'AGPL-3',
 'maintainer': 'Miteshbhimani',
 'name': 'Hospital Accounting Management',
 'summary': 'Native Odoo Accounting integration for Hospital Management',
 'version': '18.0.1.4.0'}
