# -*- coding: utf-8 -*-
import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api
from urllib import parse
from odoo.http import request
from odoo import http


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        print("this is sms cash")
        sms_env = self.env['partner.sms.send']
        data = self.env['sms.smsclient'].search([('name', '=', 'SAMANA')])
        mr = self.env['mail.recipients'].search([('name', '=', 'Receipt SMS')])
        sender = mr.user_ids
        # sender = self.env['res.users'].search(
        #     [('login', 'in', ['baig@globalmigration.co.uk'])])
        print(sender)
        message = "Dear " + self.partner_id.name + "\n" + "We have received your payment amounting AED"+str(
            '{:,.2f}'.format(self.amount)) + " (Receipt # "+self.name+"). Thank you"+"\n\nRegards,\nSD"
        print(message)
        for line in self.partner_id:
            penalty_pdf = self.env.ref('sd_receipts_report.action_report_payment_receipt_customer_copy').sudo()._render_qweb_pdf(
                [self.id], data=None)[0]
            penalty_report = base64.b64encode(penalty_pdf)

            report_name_penalty = 'Receipt Voucher'
            filename_penalty = "%s.%s" % (report_name_penalty, "pdf")
            penalty_form_attach = self.env['ir.attachment'].create({
                'name': filename_penalty,
                'datas': penalty_report,
                'store_fname': filename_penalty,
                'type': 'binary',
            })
            email_template = self.env.ref('posting_email_sms.receipts_email')
            # outgoing_server = rec.env['ir.mail_server'].search([('name','=','alert@samanadevelopers.com')])
            if email_template.mail_server_id:
                email_template.email_from = email_template.mail_server_id.name
            email_template.attachment_ids = [(6, 0, [penalty_form_attach.id])]
            # email_template.email_to = 'rashid@samana-group.com'
            email_template.send_mail(self.id, force_send=True)

            if line.mobile:
                if data:
                    # if not self._check_permissions():
                    #     raise UserError(_('You have no permission to access %s') % (data.name,))
                    url = data.url
                    name = url
                    if data.method == 'http':
                        prms = {}
                        for p in data.property_ids:
                            if p.type == 'user':
                                prms[p.name] = p.value
                            elif p.type == 'password':
                                prms[p.name] = p.value
                            elif p.type == 'to':
                                prms[p.name] = line.mobile
                            elif p.type == 'sms':
                                prms[p.name] = data.text
                            elif p.type == 'extra':
                                prms[p.name] = p.value
                            elif p.type == 'type':
                                prms[p.name] = p.value
                            elif p.type == 'source':
                                prms[p.name] = p.value
                        # prms['type'] = 0
                        # prms['source'] = 'SD'
                        prms['message'] = message
                        prms['destination'] = line.mobile[1:]

                        params = parse.urlencode(prms)
                        name = url + params
                        # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=GMS&message=dfdf&destination=923136340004"
                    # urlopen(
                    # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=SD&message=newmessage&destination=923136340004")
                    queue_obj = self.env['sms.smsclient.queue']
                    vals = {
                        'name': name,
                        'gateway_id': data.id,
                        'state': 'draft',
                        'mobile': line.mobile,
                        'msg': prms['message'],
                        # 'validity': data.validity,
                        # 'classes': data.classes1,
                        # 'deffered': data.deferred,
                        # 'priorirty': data.priority,
                        # 'coding': data.coding,
                        # 'tag': data.tag,
                        # 'nostop': data.nostop1,
                    }
                    send_sms = queue_obj.create(vals)
                    sms = self.env["sms.smsclient"]
                    sms._check_queue()
        return res