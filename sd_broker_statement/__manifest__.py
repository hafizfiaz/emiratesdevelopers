{
    'name': "Broker Statement",
    'version': '14.0',
    'summary': 'Broker Statement',
    'category': 'CRM',
    'description': """Broker Statement""",
    'author': 'Muuhammad Usman',
    "depends": ['base', 'crm', 'spa_customizations', 'account_pdc', 'commission_extension'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'reports/header_layout.xml',
        'reports/template.xml',
        'view/view.xml',
        'wizard/wizard.xml',
    ],
    "installable": True
}
