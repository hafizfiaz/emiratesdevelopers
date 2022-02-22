{
    'name': "Account Voucher Replace",
    'version': '12.0',
    'summary': 'Account Voucher Replace',
    'category': 'Accounting',
    'description': """Account Voucher Replace""",
    'author': 'Tahir Noor',
    "depends" : ['base','account','account_voucher_collection'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'view/view.xml',
        'view/email_templates.xml',
        # 'wizard/wizard.xml',
    ],
    "installable": True
}
