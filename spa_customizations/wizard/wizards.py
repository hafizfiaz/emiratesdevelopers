# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class CancelSpaWiz(models.Model):
    _name = "cancel.spa.wiz"
    _description = "Cancel SPA Wiz"

    sale_order_id = fields.Many2one('sale.order','Sale Order')

    def action_cancel(self):
        invoice_ids = []
        inv_obj = self.env['account.move']
        if self.sale_order_id:
            for line in self.sale_order_id.sale_payment_schedule_ids:
                line.state = 'cancel'
                line.installment_status = 'cancel'
                if line.invc_id:
                    print(line.invc_id)
                    if line.invc_id.state not in ['draft','cancel']:
                        invoice_ids.append(line.invc_id.id)
            # for invc in self.sale_order_id.invoice_ids:
            #     if invc.id not in invoice_ids:
            #         invoice_ids.append(invc.id)
            if self.sale_order_id.other_charges_inv_ids:
                for oci in self.sale_order_id.other_charges_inv_ids:
                    if oci.state not in ['draft', 'cancel']:
                        invoice_ids.append(oci.id)
            if not invoice_ids:
                self.sale_order_id.action_cancel()
                self.sale_order_id.property_id.write({'state': 'draft'})
            # elif invoice_ids:
            #     for invoice in inv_obj.browse(invoice_ids):
            #         # _logger.error('invoice_ids =================================== : %s' % invoice_ids)
            #         # print(invoice_ids)('payment_state', '!=', 'reversed')
            #         # if not invoice.credit_note_id or invoice.credit_note_id.state == 'cancel':
            #         if invoice.payment_state != 'reversed':
            #             raise ValidationError("If you want to cancel SPA, please add credit note against all invoices")
            self.sale_order_id.action_cancel()
            self.sale_order_id.property_id.write({'state': 'draft'})


class ReviewWiz(models.Model):
    _name = "is.buy.review"
    _description = "Booking Review"

    name = fields.Char('Name', readonly=True)
    booking_id = fields.Many2one('sale.order', 'Booking')

    def action_is_buy_review(self):
        self.booking_id.write({'state': 'review'})


class LegalReviewWiz(models.TransientModel):
    _name = "submit.legal.review"
    _description = "Submit Legal Review SPA"

    name = fields.Char('Name', readonly=True)
    sale_id = fields.Many2one('sale.order', 'SPA')

    def action_apply(self):
        if self.sale_id:
            self.sale_id.write({'state': 'under_legal_review'})
            for line in self.sale_id.sale_payment_schedule_ids:
                if line.state != 'confirm':
                    line.state = 'confirm'


class SPALegalReview(models.TransientModel):
    _name = "spa.legal.review"
    _description = "SPA Legal Review"

    file = fields.Binary('Attachment', required=True)
    remarks = fields.Text('Remarks')
    sale_id = fields.Many2one('sale.order', 'SO')

    def action_legal_verify(self):
        self.sale_id.write({
                            'state': 'under_legal_review'
                            })
        # attachment = self.env['ir.attachment'].create({
        #     'datas': self.file,
        #     'name': 'Test mimetype gif',
        #     'datas_fname': 'file.gif'})
        attachment = self.env['ir.attachment'].create({
            'datas': self.file,
            'name': 'legal_doc.pdf',
            'type': 'binary'})
        # attachment = self.env['ir.attachment'].create({
        #     'type': 'binary',
        #     'name': 'INV/2020/0011.pdf',
        #     'res_model': 'mail.compose.message',
        #     'datas': self.sample_bill_preview,
        # })
        self.sale_id.message_post(subject='Legal Review',
                                  body=self.remarks,
                                  attachment_ids=attachment.ids)


class SPAAccountReview(models.TransientModel):
    _name = "spa.account.review"
    _description = "SPA Account Review"

    # file = fields.Binary('Attachment', required=1)
    remarks = fields.Text('Remarks', required=True)
    sale_id = fields.Many2one('sale.order', 'SO')


    def action_account_verify(self):
        self.sale_id.write({
                            'state': 'under_accounts_verification'
                            })

        self.sale_id.message_post(subject='Accounts Review',
                                  body=self.remarks)


class SPAGmReview(models.TransientModel):
    _name = "spa.gm.review"
    _description = "SPA GM Review"

    # file = fields.Binary('Attachment', required=1)
    remarks = fields.Text('Remarks', required=True)
    sale_id = fields.Many2one('sale.order', 'SO')


    def action_gm_verify(self):
        self.sale_id.write({
                            'state': 'under_approval'
                            })
        self.sale_id.message_post(subject='GM Review',
                                  body=self.remarks)


class InvoiceType(models.Model):
    _name = "invoice.type"
    _description = "Invoice Type"

    name = fields.Char('Name', required=True)
    active = fields.Char('Active', default=True)
