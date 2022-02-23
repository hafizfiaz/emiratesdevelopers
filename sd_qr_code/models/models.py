# -*- coding: utf-8 -*-
import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api
from odoo.http import request
from odoo import http


# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#     qr_image = fields.Binary("QR Code", attachment=True, store=True)
#
#     @api.model
#     def get_qr(self):
#         records = self.env['sale.order'].search([('state', 'not in', ['cancel','refund_cancellation'])])
#         a = 1
#         for rec in records:
#             print(a)
#             a += 1
#             qr = qrcode.QRCode(
#                 version=1,
#                 error_correction=qrcode.constants.ERROR_CORRECT_L,
#                 box_size=10,
#                 border=4,
#             )
#             rec_id = rec.id
#             qr.add_data(request.httprequest.host_url + 'developers?model=sale&rec_id=%s' % (rec_id))
#             qr.make(fit=True)
#             img = qr.make_image()
#             temp = BytesIO()
#             img.save(temp, format="PNG")
#             qr_image = base64.b64encode(temp.getvalue())
#             rec.qr_image = qr_image
#
#     @api.multi
#     def write(self, vals):
#         # print("Res123sale")
#         res = super(SaleOrder, self).write(vals)
#         # total = 0.0
#         # print(res)
#         if vals.get('state'):
#             if vals.get('state') not in ['cancel','refund_cancellation']:
#                 qr = qrcode.QRCode(
#                     version=1,
#                     error_correction=qrcode.constants.ERROR_CORRECT_L,
#                     box_size=10,
#                     border=4,
#                 )
#                 rec_id = self.id
#                 qr.add_data(request.httprequest.host_url + 'developers?model=sale&rec_id=%s' % (rec_id))
#                 qr.make(fit=True)
#                 img = qr.make_image()
#                 temp = BytesIO()
#                 img.save(temp, format="PNG")
#                 qr_image = base64.b64encode(temp.getvalue())
#                 self.qr_image = qr_image
#         return res

class AccountPayment(models.Model):
    _inherit = "account.payment"

    # image = fields.Binary("QR Code", attachment=True, store=True)
    qr_image = fields.Binary("QR Code", attachment=True, store=True)
    # qr_image = fields.Binary("QR Code", attachment=True, store=True)

    @api.model
    def get_qr(self):
        records = self.env['account.payment'].search([('state', 'in',['posted','collected','deposited'])])
        a = 1
        for rec in records:
            print(a)
            a += 1
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            rec_id = rec.id
            qr.add_data(request.httprequest.host_url + 'developers?model=payment&rec_id=%s' % (rec_id))
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            # rec.qr_image = qr_image
            rec.qr_image = qr_image


    def write(self, vals):
        print("Res123payment")
        res = super(AccountPayment, self).write(vals)
        # total = 0.0
        print(res)
        if vals.get('state'):
            if vals.get('state') in ['posted','collected','deposited']:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                rec_id = self.id
                qr.add_data(request.httprequest.host_url + 'developers?model=payment&rec_id=%s' % (rec_id))
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                self.qr_image = qr_image
        return res

# class AccountPDC(models.Model):
#     _inherit = "account.voucher.collection"
#     qr_image = fields.Binary("QR Code", attachment=True, store=True)
#
#     @api.model
#     def get_qr(self):
#         records = self.env['account.voucher.collection'].search([('state', 'in', ['collected'])])
#         a = 1
#         for rec in records:
#             print("multipayment"+str(a))
#             a += 1
#             qr = qrcode.QRCode(
#                 version=1,
#                 error_correction=qrcode.constants.ERROR_CORRECT_L,
#                 box_size=10,
#                 border=4,
#             )
#             rec_id = rec.id
#             qr.add_data(request.httprequest.host_url + 'developers?model=multipayment&rec_id=%s' % (rec_id))
#             qr.make(fit=True)
#             img = qr.make_image()
#             temp = BytesIO()
#             img.save(temp, format="PNG")
#             qr_image = base64.b64encode(temp.getvalue())
#             rec.qr_image = qr_image
#
#     @api.multi
#     def write(self, vals):
#         print("Res123multipayment")
#         res = super(AccountPDC, self).write(vals)
#         # total = 0.0
#         print(res)
#         if vals.get('state'):
#             if vals.get('state') in ['collected']:
#                 qr = qrcode.QRCode(
#                     version=1,
#                     error_correction=qrcode.constants.ERROR_CORRECT_L,
#                     box_size=10,
#                     border=4,
#                 )
#                 rec_id = self.id
#                 qr.add_data(request.httprequest.host_url + 'developers?model=multipayment&rec_id=%s' % (rec_id))
#                 qr.make(fit=True)
#                 img = qr.make_image()
#                 temp = BytesIO()
#                 img.save(temp, format="PNG")
#                 qr_image = base64.b64encode(temp.getvalue())
#                 self.qr_image = qr_image
#         return res