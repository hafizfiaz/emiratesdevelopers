# -*- coding: utf-8 -*-
#===============================================================================
# '''
# Created on 2 mars 2018
# 
# @author: user
# '''
# 
#===============================================================================

# import time
# from odoo.report import report_sxw
#
#
# STATE_LABEL = {
#     'draft':'Draft',
#     'cancel':'Cancelled',
#     'proforma':'Pro-forma',
#     'pending':'Pending for Collection',
#     'collected':'Collected',
#     'outsourced':'Outsourced',
#     'paid_unposted':'Deposit/InCashed',
#     'posted':'Posted',
#     'refused':'Bounced',
#     'withhold':'WithHold',
#     'replaced':'Replaced'
#     }


# class account_voucher_collection_report(report_sxw.rml_parse):
#     def __init__(self, cr, uid, name, context):
#         super(account_voucher_collection_report, self).__init__(cr, uid, name, context=context)
#         self.localcontext.update({
#             'time': time,
#             'get_label_state': self._get_label_state,
#             'get_amount_in_aed': self._get_amount_in_aed,
#         })
#
#     def _get_label_state(self, state):
#         return STATE_LABEL.get(''+state+'')
#
#     def _get_amount_in_aed(self, line):
#         currency_obj = self.pool.get('res.currency')
#         amount = line.amount
#         if line.currency_id != line.company_id.currency_id:
#             amount = currency_obj.compute(self.cr, self.uid, line.currency_id.id, line.company_id.currency_id.id, amount)
#         return amount
        
# report_sxw.report_sxw('report.account.voucher.collection.print', 'account.voucher.collection', 'addons/account_voucher_collection/report/account_voucher_collection.rml', parser=account_voucher_collection_report, header="external")
