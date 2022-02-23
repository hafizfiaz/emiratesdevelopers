{
    'name': "Commission Extension",
    'version': '12.4',
    'summary': 'It will change the commission flow',
    'category': 'Accounting',
    'description': """It will change default commission flow""",
    'author': 'Tahir Noor',
    "depends" : ['base','property_commission','property_management'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'view/email_template.xml',
        'view/commission_type.xml',
        'view/view.xml',
        'view/spa.xml',
        'Wizard/create_commission.xml',
    ],
    "installable": True
}
