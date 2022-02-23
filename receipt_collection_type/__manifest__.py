# -*- coding: utf-8 -*-
{
    'name' : 'Receipt Collection Type',
    'version' : '14.0',
    'author' : 'Muhammad Rashid Mukhtar',
    'description': """
PDC Module
=======================
Post Dated Cheques1.
    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.samana-group.com',
    'depends' : [
        'base',
        'account_pdc',
        'account_voucher_collection',
        ],
    'demo' : [],
    'data' : [
        'views/pdc_view.xml',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
}
