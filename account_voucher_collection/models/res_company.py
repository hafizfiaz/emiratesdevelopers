# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class res_company(models.Model):
    _inherit = 'res.company'
    

    payment_note = fields.Html('Terms and Conditions for Payment', translate=True, help="Default terms and conditions for Payments.",
        default="""
        1.Customer hereby confirms that the above cheques are thoroughly verified by him before releasing and found correct in regards to date,
         signature and other aspects. GMS is not liable at all if cheque is bounced or returned due to wrong date or missing signature.
        2.All these cheques will be outsourced to our bank. Therefore it is not possible to replace any cheque.
        3.The Outsourced cheques can be withdrawn by paying cash against cheques one week before the due
          date of cheques. charges for withdrawal of cheques are AED 50. - Per Cheque.
        4.Bounced cheques will be charged Dhs. 200 - per cheque    
        """)
    fax = fields.Char(string='Fax')
