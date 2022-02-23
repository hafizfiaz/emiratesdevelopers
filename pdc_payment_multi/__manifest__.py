# -*- coding: utf-8 -*-
{
    'name' : 'Multi PDC Payment',
    'version' : '1.0',
    'author' : 'Tahir Noor',
    'description': """
Multi PDC Payment
=======================
multi PDC Payment..
    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.odoo.com',
    'depends' : [
        # 'account_voucher',
        'account_pdc',
        'account_voucher_collection',
        'account',
        'account_payment',
        'property_management',
        'ow_account_asset',
        #'sale_shop'
        ],
    'demo' : [],
    'data' : [
        'data/multi_pdc_payment_sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/multi_pdc_payment.xml',
        #HRN
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
