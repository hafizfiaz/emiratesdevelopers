# -*- coding: utf-8 -*-


{
    'name': "Early Settlement",

    'summary': """EarlySettlement""",
    'author': 'Muhammad Usman Zameer',
    'description': """
    """,

    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'sale', 'crm','spa_customizations','property_management','sale_amendment'],
    'data': [
        'security/ir.model.access.csv',
        'views/earlysettlement.xml',
        'views/discount_type.xml',
        'views/sequence.xml',
        'report/report.xml',
        'report/earlysettlmentreport.xml'
    ],
    'demo': [],
}
