{
    'name': "SD Payment Reconcile",
    'version': '14.0',
    'summary': 'SD Payment Reconcile Module',
    'category': 'CRM',
    'description': """SD Payment Reconcile""",
    'author': 'Tahir Noor',
    "depends" : ['base','account','spa_customizations','commission_extension'],
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'view/view.xml',
        # 'wizard/wizard.xml',
    ],
    "installable": True
}
