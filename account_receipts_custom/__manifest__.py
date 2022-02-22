{
    'name': "Receipts Custom",
    'version': '12.0',
    'summary': 'Receipts Custom',
    'category': 'Accounting',
    'description': """Receipts Custom""",
    'author': 'Tahir Noor',
    "depends" : ['base','account','account_pdc','account_voucher_collection'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'view/view.xml',
        'wizard/wizard.xml',
    ],
    "installable": True
}
