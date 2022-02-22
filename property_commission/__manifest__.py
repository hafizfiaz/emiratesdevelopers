# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

{
    'name': 'Property Commission',
    'version': '12.0.1.0.0',
    'category': 'Real Estate',
    'description': """
        Property Management System

        This module gives the features for create property with gross value, number
        of towers, ground rent etc. also create sub property. where you can mentions
        Parent Property,number of floors , properties per floor,etc. and show sub
        property status either it's available or booked or any other states.
     """,
    'author': 'Tahir Noor',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management','spa_customizations'],
    'data': [
            'data/commission_seq.xml',
            'security/res_groups.xml',
            'security/ir.model.access.csv',
            'views/property_commission_view.xml',
            'views/property_res_partner_views.xml',
            'report/commission_report_template2.xml',
            'views/report_configuration.xml',

    ],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
