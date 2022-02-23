{
    'name': "PDC Movements",
    'version': '12.0',
    'summary': 'Movements report',
    'category': 'Accounting',
    'description': """Movements report""",
    'author': 'Muhammad Rashid Mukhtar',
    "depends" : ['base','account_pdc','settlement'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        # 'data/data.xml',
        # 'reports/layout.xml',
        'reports/teplate.xml',
        'view/view.xml',
        'wizard/wizard.xml',
        'wizard/wizard_bounced.xml',
        'wizard/wizard_security.xml',
        'wizard/wizard_receivable_summary.xml',
        'wizard/wizard_profit_loss.xml',
        'wizard/wizard_sales_expense.xml',
    ],
    "installable": True
}
