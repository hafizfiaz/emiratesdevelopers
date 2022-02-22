{
    'name': "Cash FlowReport",
    'version': '12.0',
    'summary': 'Cash flow report',
    'category': 'Accounting',
    'description': """cashflow report""",
    'author': 'Muhammad Rashid Mukhtar',
    "depends" : ['base','account'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        # 'data/data.xml',
        # 'reports/layout.xml',
        'reports/teplate.xml',
        # 'view/view.xml',
        'wizard/wizard.xml',
    ],
    "installable": True
}
