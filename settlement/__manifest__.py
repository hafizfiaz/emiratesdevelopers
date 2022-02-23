#-*- coding: utf-8 -*-
{
   'name': 'Settlement',
    'description': """
        It will add Settlement under Accounting
        """,
    'version':'1.0.0',
    'category': 'Accounting',
    'author': 'Tahir Noor',
    'website': 'http://www.odoo.com',
    'depends':['base','account','account_pdc','ow_account_asset'],
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,

}
