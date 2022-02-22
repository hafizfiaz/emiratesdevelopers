# -*- coding: utf-8 -*-


{
    'name': "Refund EOI",

    'summary': """SD Refund EOI""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.odoo.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'crm', 'sale','spa_customizations','property_management','settlement'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/sales_group.xml',
        'views/refund_eoi.xml',
        'views/sequence.xml',
        'views/email.xml',

    ],
    'demo': [],
}
