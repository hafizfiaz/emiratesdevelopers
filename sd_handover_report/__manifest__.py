# -*- coding: utf-8 -*-


{
    'name': "HANDOVER REPORT",

    'summary': """Handover Report""",

    'description': """
    """,

    'author': 'Muhammad Usman Zameer',
    'depends': ['base', 'account', 'crm', 'sale', 'spa_customizations'],
    'data': [
        'report/reports.xml',
        'report/handover_report.xml',
        'views/journal_entry.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
}
