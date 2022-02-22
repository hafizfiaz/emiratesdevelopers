{
    'name': "SPA Charges invoices",
    'version': '14.0',
    'summary': 'SPA Charges invoices',
    'category': 'CRM',
    'description': """SPA Charges invoices""",
    'author': 'Tahir Noor',
    "depends" : ['base','spa_customizations'],
    'data': [
        'security/ir.model.access.csv',
        'view.xml',
    ],
    "installable": True
}
