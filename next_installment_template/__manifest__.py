# -*- coding: utf-8 -*-
{
    'name' : 'Next Installment Template',
    'version' : '1.0',
    'author' : 'Muhammad Rashid Mukhtar',
    'description': """
PDC Module
=======================
Post Dated Cheques.
    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.samana-group.com',
    'depends' : [
        'base',
        'spa_customizations',
        'account_pdc',
        'fgr_payment_request',
        'sd_receipts_report',
        'account_receipts_custom',
        ],
    'demo' : [],
    'data' : [
        'views/view.xml',
    ],
    'installable': True,
}
