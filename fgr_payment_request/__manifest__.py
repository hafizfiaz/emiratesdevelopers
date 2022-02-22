#-*- coding: utf-8 -*-
{
   'name': 'FGR Payment Request',
    'description': """FGR Payment Request Module Details""",
    'version':'1.0.2',
    'category': 'Accounting',
    'author': 'Tahir Noor',
    'website': 'http://www.odoo.com',
    'depends':['base','spa_customizations','property_management','project','account_receipts_custom'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/view.xml',
        # 'views/report.xml',
    ],
    'installable': True,
}
