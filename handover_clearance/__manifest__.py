# -*- coding: utf-8 -*-


{
    'name': "SD HANDOVER CLEARANCE",

    'summary': """Sd Handover Clearance""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail','crm', 'sale', 'spa_customizations','property_management','ow_account_asset','sd_account_clearance'],
    'data': [
        'security/ir.model.access.csv',
        'views/sequence.xml',
        'views/handoverclearance.xml'

    ],
    'demo': [],
}
