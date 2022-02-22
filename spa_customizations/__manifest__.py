{
    'name': "SPA Customizations",
    'version': '12.1',
    'summary': 'SPA Customizations',
    'category': 'Accounting',
    'description': """SPA Customizations and related models""",
    'author': 'Tahir Noor',
    "depends": ['base', 'account', 'sale', 'sale_crm', 'sales_team', 'sale_management', 'property_management',
                'account_pdc','security_groups'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/property.xml',
        'views/premium.xml',
        'views/actions_menus.xml',
        'wizard/wizards.xml',
        'views/res_partner.xml',
        'views/spa.xml',
        'views/receivable_status.xml',
        'views/inventory_status.xml',
        'views/payment_schedule.xml',
        'views/discount.xml',
        'views/sale_rent_schedule.xml',
        'views/commission_type.xml',
        'views/invoice.xml',
        'views/dld_schedule.xml',
        'views/spa_summary.xml',
        'views/schedule_view.xml',
        'wizard/remove_schedule_wiz.xml',
        'reports/reports.xml',
        'reports/report_layout.xml',
        'reports/sale_agreement.xml',
        'reports/golf_print.xml',
    ],
    "installable": True
}