# -*- coding: utf-8 -*-


{
    'name': "SD ACCOUNT CLEARANCE",

    'summary': """Sd Account Clearance""",

    'description': """Account Clearance
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'crm', 'sale', 'spa_customizations', 'property_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/accountsclearance.xml',
        'views/clearance_type_form.xml',
        'views/sequence.xml'
    ],
    'demo': [],
}
