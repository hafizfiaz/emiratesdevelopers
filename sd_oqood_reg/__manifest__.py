# -*- coding: utf-8 -*-


{
    'name': "SD Oqood Registration",

    'summary': """Oqood Registration""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'crm','sale','sd_account_clearance', 'sd_stage_changes','spa_customizations','property_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/oqood_reg.xml',
        'views/sequence.xml'
        
    ],
    'demo': [],
}
