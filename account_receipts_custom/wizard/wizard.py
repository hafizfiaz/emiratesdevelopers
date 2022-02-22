# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class UnallocatedDraftWiz(models.TransientModel):
    _name = "unallocated.draft.wiz"

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    unallocated_check = fields.Boolean(string='Unallocated Receipts')
    draft_check = fields.Boolean(string='Draft Receipts')
    # recipients_id = fields.Many2one('mail.recipients',string='Recipients')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    def get_result(self):
        receipt_list = []
        domain =[('payment_type','=','inbound')]
        if self.start_date:
            domain.append(('payment_date', '>=', self.start_date))
        if self.end_date:
            domain.append(('payment_date', '<=', self.end_date))
        if self.draft_check:
            receipt_list = []
            domain.append(('state', '=', 'draft'))
            receipt_ids = self.env['account.payment'].search(domain)
            for rec in receipt_ids:
                receipt_list.append(rec.id)
        if self.unallocated_check:
            receipt_list = []
            domain.append(('state', 'not in', ['draft','cancelled']))
            domain.append(('booking_id', '=', False))
            receipt_ids = self.env['account.payment'].search(domain)
            for rec in receipt_ids:
                if rec.invoice_ids or rec.reconciled_invoice_ids:
                    receipt_list.append(rec.id)
        if self.draft_check and self.unallocated_check:
            receipt_list = []
            domain.append(('state', '=', 'draft'))
            domain.append(('state', 'not in', ['draft','cancelled']))
            domain.append(('booking_id', '=', False))
            receipt_ids = self.env['account.payment'].search(domain)
            for rec in receipt_ids:
                if rec.invoice_ids or rec.reconciled_invoice_ids:
                    receipt_list.append(rec.id)

        print('abc')
        return {
            'name': _("Receipts"),
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id','in',receipt_list)],
        }
