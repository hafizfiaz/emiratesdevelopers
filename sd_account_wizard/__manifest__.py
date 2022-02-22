# -*- coding: utf-8 -*-


{
    'name': "PDCs Account Wizard",

    'summary': """Account Wizard""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail','crm','account','spa_customizations','account_pdc'],
    'data': [
        'security/ir.model.access.csv',
        'views/view.xml',
        'wizard/pdcwizard.xml'
    ],
    'demo': [],
}
