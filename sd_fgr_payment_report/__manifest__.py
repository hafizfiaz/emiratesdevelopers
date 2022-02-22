# -*- coding: utf-8 -*-


{
    'name': "SD FGR Payment Report",

    'summary': """FGR Payment Request Report""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'fgr_payment_request'],
    'data': [
        'reports/report.xml',
        'reports/layout.xml',
        'reports/customer_statement_with_penalty.xml',
        'reports/fgr_schedule.xml'
    ],
    'demo': [],
}
