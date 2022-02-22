# -*- coding: utf-8 -*-
{
   'name': 'Payment Purchase Invoice',
    'description': """
        Add invoice invoice field in payment.
        """,
    'version':'12.0.0.1',
    'author': 'Tahir Noor',
    'website': 'http://www.samana-group.com',
    'depends':['base','account_pdc'],
    'data': [
        'views/view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,

}