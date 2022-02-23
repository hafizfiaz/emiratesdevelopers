# -*- coding: utf-8 -*-


{
    'name': "SD Company Field Inherit",

    'summary': """Company Field Inherit""",

    'description': """
    """,

    'author': "Muhammad Usman Zameer",
    'website': "http://www.yourcompany.com",
    'category': 'Test',
    'version': '0.1',
    'depends': ['base', 'sale', 'account', 'spa_customizations', 'property_management', 'account_pdc',
                'handover_clearance', 'sd_account_clearance', 'termination_process', 'sd_early_settlement',
                'sd_refund_eoi', 'sd_oqood_reg', 'bi_sms_client_generic', 'sms_notification', 'sd_project_costing',
                'sd_payment_certificate','hr_appraisal','custom_approvals','sale_amendment','calendar','sd_courier'],
    'data': [
        'views/view.xml'
    ],
    'demo': [],
}
