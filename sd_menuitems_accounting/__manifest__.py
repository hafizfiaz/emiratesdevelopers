{
    'name': "SD ACCOUNTING MENUITEMS",
    'version': '14.0',
    'summary': 'SD Accounting Menuitems',
    'category': 'Accounting',
    'description': """Accounting Menuitems""",
    'author': 'Muhammad Usman Zameer',
    "depends": ['base', 'crm', 'account', 'sale', 'spa_customizations', 'sales_team', 'sd_menuitems_crm',
                'account_voucher_collection', 'property_management','sd_web_status_ext'],
    'data': [
        'view/view.xml',
    ],
    "installable": True
}
