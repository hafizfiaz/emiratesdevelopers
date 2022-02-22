# -*- coding: utf-8 -*-


{
    'name': "SD Termination Process",

    'summary': """Termination Process""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'account', 'crm', 'sale', 'spa_customizations', 'sd_account_clearance',
                'property_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sequence.xml',
        'views/termination_process.xml'

    ],
    'demo': [],
}
