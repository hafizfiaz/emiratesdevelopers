{
'name' : 'Sale Amendment',
'version' : '12.0',
'author' : 'Muhammad Rashid Mukhtar',
'description' : 'Client Type (Temporary & Permanent)',
'category': 'Sale',
'depends' : ['base','crm','sales_team','sale','spa_customizations','sd_sale_order_report', 'property_management'

             ],
'data' : [
        # 'report/report.xml',
        'report/amendment_report.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
          ],
'demo' : [],
'installable' : True,
}
