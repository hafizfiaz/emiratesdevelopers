# -*- coding: utf-8 -*-
{
    'name' : 'Customer Payments Multi',
    'version' : '1.0',
    'author' : 'Tahir Noor',
    'description': """
Customer Payments Multi
=======================
Customer Payment Multi (More than One Collection i.e Multi PDC, PDC &amp; cash, Credit Card &amp; Cash). 
This document as a whole should have separate Serial Number to manage.
Multi Collection Customer Payment Form Should be like same as Existing Customer Payment form with Branch Selection Option for Print Out.
Customer Payment Multi collect only the payment (cheques) but it don't reconcile the invoices.
THe user will do the reconciliation manually with the invoices on the system after the Cheque is collected on Customer Payment Multi

Document Top Fields
-Customer
-Mobile
-Date
-Payment Ref
-Memo
-Company
-Branch (If we want to change the print out- same as in sale order)

Tab: Collection
In this Tab option of “Add Customer Payment” and when I click to this we can fill the line here not open new form directly on first place. 
End of each line the symbol or ARROW where we click and open full form (same as customer payment form) should open. 
Each line or form should take auto information from the top form fields like Customer name, mobile, Date, ………. 
Rest information user will fill accordingly whatever he is collecting. 
Now through Add Customer payment option even user can collect “Cash, Credit Card &amp; PDC” from a single customer against one invoice and again one main document.
All lines of payment Total should be calculated at down.
This is Just Multi Collection. 
After Save Posting of each customer payment line shall be same as existing single customer Payment.
    """,
    'category': 'Accounting & Finance',
    'website' : 'http://www.odoo.com',
    'depends' : [
        'account_pdc',
        'sale',
        'crm',
        'account',
        'account_payment',
        'ow_account_asset',
        'account_accountant',
        #'sale_shop'
        ],
    'demo' : [],
    'data' : [
        'views/accounting_menu.xml',
        'views/account_voucher_collection_view.xml',
        'views/voucher_payment_receipt_view.xml',
        'security/ir.model.access.csv',
        'data/account_voucher_collection_sequence.xml',
        # 'views/account_voucher_collection_report.xml',
        'views/res_company_view.xml',
        'views/crm_view.xml',
        #HRN 2018-05-10
        'security/account_voucher_collection_security.xml',
        'report/customer_payment_multi_template.xml',
        'report/customer_payment_multi.xml',
        #HRN
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
