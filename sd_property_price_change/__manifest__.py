{
    'name': "Change Property Price",
    'version': '14.0',
    'summary': 'Change Property Price',
    'category': 'CRM',
    'description': """Change Property Price""",
    'author': 'Muhammad Usman Zameer',
    "depends" : ['base','sd_web_status_ext','ow_account_asset'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/data.xml',
        # 'view/view.xml',
        'wizard/wizard.xml',
    ],
    "installable": True
}
