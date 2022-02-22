# -*- coding: utf-8 -*-


{
    'name': "SD Payment Certificate",

    'summary': """Payment Certificate""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'account', 'crm', 'sale', 'spa_customizations', 'sd_account_clearance',
                'property_management', 'sd_project_costing'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_certificate.xml'
    ],
    'demo': [],
}
