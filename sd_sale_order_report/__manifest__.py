# -*- coding: utf-8 -*-


{
    'name': "SPA REPORTS",

    'summary': """SD Sale Order Reports""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'sale', 'spa_customizations','account_pdc'],
    'data': [
        'views/sale_order_changes.xml',
        'reports/report.xml',
        'reports/customer_statement_with_penalty.xml',
        'reports/closure_form.xml',
        'reports/expression_of_interest.xml',
        'reports/agent_eoi.xml',
        'reports/reservation_print.xml'
    ],
    'demo': [],
}
