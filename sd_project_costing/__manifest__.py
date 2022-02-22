# -*- coding: utf-8 -*-


{
    'name': "SD Project Costing",

    'summary': """Project Costing""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'mail', 'account', 'crm', 'property_management', 'sd_stage_changes', 'account_pdc',
                'sd_costing_contractor'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_costing.xml',
        'views/sequence.xml'
    ],
    'demo': [],
}
