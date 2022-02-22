# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SPASummaryView(models.TransientModel):
    _name = 'spa.summary.view'
    _description = 'SPA Summary View'

    sale_id = fields.Many2one('sale.order', 'Related SPA/Booking')

    amount_untaxed = fields.Float('Untaxed Amount')
    amount_tax = fields.Float('Taxes')
    amount_total = fields.Float('Total SPA Value')
    amount_till_date = fields.Float('Total Installments Payable Till Date')
    paid_installments = fields.Float(string="Paid Installments", help="sum of received amount from installments")
    paid_installments_perc = fields.Float(string="Paid Installments %", help="(Paid Installments / Total Property Sale Value) *100")
    matured_pdcs_perc = fields.Float(string="Total Realized Collection %", help="(Amount Received (Realized Collections)/ Total SPA Value) *100")
    unsecured_collections_perc = fields.Float(string="Total Unsecured Collections %", help="Total Unsecured Collections / Total SPA Value) *100")
    pending_balance = fields.Float('Pending Collections',
                                   help='Total SPA Value - Total Collections')

    balance_due_collection = fields.Float('Balance Due Collection',
                                          help='Total Due Amount - Amount Received (Realized Collections)')
    total_unsecured_collections = fields.Float('Total Unsecured Collections',
                                               help='Sum of Non-matured + Uncleared + Held + Bounced Cheques')
    installment_balance_pending = fields.Float('Balance Due Installment',
                                               help='Installments Due - Paid Installments')
    instalmnt_bls_pend_plus_admin_oqood = fields.Float('Total Due Amount', help='Installment Payable till Date + Oqood charged + Admin Charged + Other Charges')
    pending_balance_perc = fields.Float('Pending Collections (%)', help='Pending Collections /Total SPA Value*100')
    receipts_perc = fields.Float('Total Collections % ', help='Total Collections/Total SPA Value*100')
    matured_pdcs = fields.Float('Amount Received (Realized Collections)', help='All Posted Receipts')
    hold_pdcs = fields.Float('Cheques Held')
    deposited_pdcs = fields.Float('Uncleared Cheques',help="PDCs in Deposited Status")
    un_matured_pdcs = fields.Float('Non-Matured Collections', help="PDCs in Pending for Collection and Collected Status")
    bounced_pdcs = fields.Float('Bounced Cheque', help="PDCs in Bounced Status")
    total_receipts = fields.Float('Total Collections', help="Total Receipts where state not in 'draft','proforma',"
                                                      "'cancelled','refused','rejected','replaced','outsourced'")
    total_spa_value = fields.Float('Total SPA Value', help='Property Price + Oqood charged + Admin Charged + Other Charges')
    #
    oqood_fee = fields.Float(string='Oqood Fee Charged')
    admin_fee = fields.Float(string='Admin Fee Charged')

    oqood_received = fields.Float('Oqood Received')
    admin_received = fields.Float('Admin Fee Received')
    balance_due_oqood = fields.Float(string="Balance Due Oqood", help="Oqood fee charged - Oqood fee received")
    balance_due_admin = fields.Float(string="Balance Due Admin Charges", help="Admin fee charged - Admin fee received")
    other_received = fields.Float(string="Other Charges Received", help="Total Reconciled amount against Add Jvs")
    balance_due_other = fields.Float(string="Balance Due Other Charges", help="Other Charges - Other Charges Received")

    escrow = fields.Float(string="Escrow Receipts")
    escrow_perc = fields.Float(string="Escrow Receipt Percentage(%)")
    non_escrow = fields.Float(string="Non Escrow Receipts")
    non_escrow_perc = fields.Float(string="Non Escrow Receipt Percentage(%)")
    total_escrow = fields.Float("Total Escrow")
    total_escrow_perc = fields.Float("Total Percentage(%)")
    other_charges = fields.Float(string='Other Charges')