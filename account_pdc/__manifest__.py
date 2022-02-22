# -*- coding: utf-8 -*-
{
    'name' : 'PDC',
    'version' : '1.1',
    'author' : 'Tahir Noor',
    'description': """
PDC Module
=======================
Post Dated Cheques.
    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.samana-group.com',
    'depends' : [
        'base',
        'account',
        'property_management',
        'ow_account_asset',
        'security_groups',
        # 'crm_extension',
        'sale',
        # 'account_cancel',
        ],
    'demo' : [],
    'data' : [
        # 'data/account_pdc_data.xml',
        'security/ir.model.access.csv',
        'security/pdc_security.xml',
        'views/account.xml',
        'views/pdc_view.xml',
        'views/collection_team.xml',
        'views/journal.xml',
        # 'views/booking_and_spa.xml',
        # 'report/paperformat_payment_receipt.xml',
        # 'report/payment_receipt.xml',
        # 'report/account_move_template.xml',
        # 'report/account_move_print.xml',
        # 'wizard/convert_pdcs.xml',
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
}
