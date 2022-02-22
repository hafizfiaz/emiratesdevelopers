{
    'name': "SD Courier",
    'version': '14.0',
    'summary': 'SD Courier',
    'category': 'CRM',
    'description': """SD Courier""",
    'author': 'Muhammad Usman Zameer',
    "depends" : ['base','crm','account','spa_customizations','property_management','ow_account_asset'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        # 'data/data.xml',
        'view/view.xml',
        # 'wizard/wizard.xml',
    ],
    "installable": True
}
