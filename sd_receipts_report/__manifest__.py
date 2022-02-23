# -*- coding: utf-8 -*-


{
    'name': "SD RECEIPT REPORTS",

    'summary': """SD Receipt Reports""",

    'description': """    """,

    'author': "Muhammad Usman Zameer",
    'version': '0.1',
    'depends': ['base', 'account', 'mail', 'account', 'spa_customizations', 'property_management','account_voucher_collection'],
    'data': [
        'report/customer_payment.xml',
        'report/pdc_acknowledgement.xml',
        'report/payment_receipt.xml',
        'report/invoices_report.xml'
    ],
    'demo': [],
}
