{
    'name': "SD Rent",
    'version': '12.0',
    'summary': 'SD Rent',
    'category': 'CRM',
    'description': """SD Rent""",
    'author': 'Tahir Noor',
    "depends" : ['base','property_management','spa_customizations'],
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'view/tenancy.xml',
        'view/view.xml',
        # 'wizard/wizard.xml',
    ],
    "installable": True
}
