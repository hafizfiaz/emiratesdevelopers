{
    'name': "Penalty Rules",
    'version': '12.0',
    'summary': 'Penalty Rules',
    'category': 'CRM',
    'description': """Penalty Rules""",
    'author': 'Tahir Noor',
    "depends" : ['base','sale','property_management','spa_customizations'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'view/view.xml',
        # 'wizard/wizard.xml',
    ],
    "installable": True
}
