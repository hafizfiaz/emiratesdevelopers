{
    'name': "Portal Extension",
    'version': '14.2',
    'summary': 'Portal Extension',
    'category': 'Sales',
    'description': """Portal Extension""",
    'author': 'Tahir Noor',
    "depends" : ['base','portal','sale'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'view/view.xml',
    ],
    "installable": True
}
