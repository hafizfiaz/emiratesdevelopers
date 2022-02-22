# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Management Website',
    'description': 'This module will help you to manage your real estate portfolio with Property valuation, Maintenance, Insurance, Utilities and Rent management with reminders for each KPIs.',
    'category': 'Website',
    'version': '12.0',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'depends': ['property_management', 'base_geolocalize','payment_paypal', 'property_penalty', 'portal' ,'website','auth_signup','survey', 'web'],
    'data': [
        'views/website_assets.xml',
        'views/assets_views.xml',
        'views/homepage_template.xml',
        'data/website_data.xml',
        'views/samana_golf.xml',
        'views/property_main_template.xml',
        'views/testimonials.xml',
        # 'views/property_login_view.xml',
        'views/rent_properties_onload.xml',
        'views/selected_property_template.xml',
        'views/suggested_property_template.xml',
        'views/sell_property_template.xml',
        'views/allpastlease_content_template.xml',
        'views/saved_sale_template.xml',
        'views/my_property_template.xml',
        'views/website_search_bar_template.xml',
        'views/website_property_pagination_template.xml',
        'views/website_property_filter.xml',
        'views/reservation_form.xml',
        'views/layout.xml',
        'views/reservation_web_template.xml',
        'views/golf_reservation_template.xml',
        # 'views/website_contactus_template.xml',
        'security/website_security.xml',
        'security/ir.model.access.csv',
        # 'data/website_data.xml',
        # 'data/website_data_no_update.xml',
        # 'view/template.xml',
        # 'view/homepage.xml',
        # 'view/featured_sales_views.xml',
        # 'view/featured_past_lease_views.xml',
        # 'view/assets.xml',
        # 'view/asset_view.xml',
    ],
    'application': True,
    'installable': True,
}
