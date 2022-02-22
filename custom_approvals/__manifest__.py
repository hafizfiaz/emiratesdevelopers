#-*- coding: utf-8 -*-
{
   'name': 'Custom Approvals',
    'description': """
        Custom Approval
        """,
    'version':'1.0.0',
    'category': 'Human Resources',
    'author': 'Tahir Noor',
    'website': 'http://www.odoo.com',
    'depends':['base','mail','account_pdc'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/view.xml',
    ],
    'installable': True,

}
