# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

import logging
import re
from os.path import isdir
from urllib.request import urlopen
from urllib import parse
from html.parser import HTMLParser
from odoo import _, api, fields, models, tools


_logger = logging.getLogger(__name__)


# http://stackoverflow.com/questions/38200739/extract-text-from-html-mail-odoo
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


class SmsTemplate(models.Model):
    "Templates for sending sms"
    _inherit = "sms.template"
    _description = 'SMS Templates'
    _order = 'name'

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char('Name', required=True)
    auto_delete = fields.Boolean("Auto Delete")
    globally_access = fields.Boolean(
        string="Global", help="if enable then it will consider normal(global) template.You can use it while sending the bulk message. If not enable the you have to select condition on which the template applies.")
    condition = fields.Selection([('order_placed', 'Order Placed'),
                                  ('order_confirm', 'Order Confirmed'),
                                  ('order_delivered', 'Order Delivered'),
                                  ('invoice_vaildate', 'Invoice Validate'),
                                  ('invoice_paid', 'Invoice Paid'),
                                  ('order_cancel', 'Order Cancelled')], string="Conditions", help="Condition on which the template has been applied.")
    model_id = fields.Many2one(
        'ir.model', 'Applies to', compute="onchange_condition", help="The kind of document with this template can be used. Note if not selected then it will consider normal(global) template.", store=True)
    model = fields.Char(related="model_id.model", string='Related Document Model',
                        store=True, readonly=True)
    sms_body_html = fields.Text('Body', translate=True, sanitize=False,
                                help="SMS text. You can also use ${object.partner_id} for dynamic text. Here partner_id is a field of the document(obj/model).", )

    # @api.onchange('globally_access')
    # def onchange_globally_access(self):
    #     if self.globally_access:
    #         self.condition = False

    def _get_partner_mobile(self, partner):
        mobile = partner.mobile if partner.mobile else partner.phone
        if not mobile:
            return False
        company_country_calling_code = self.env.user.company_id.country_id.phone_code
        managed_calling_code = self.env['ir.config_parameter'].get_param(
            'sms_notification.is_phone_code_enable', 'False') == 'True'
        if managed_calling_code:
            return mobile
        if partner.country_id and partner.country_id.phone_code:
            country_calling_code = partner.country_id.phone_code
        else:
            country_calling_code = company_country_calling_code
        return "+{code}{mobile}".format(code=country_calling_code, mobile=mobile)

    @api.depends('condition')
    def onchange_condition(self):
        if self.condition:
            if self.condition in ['order_placed', 'order_confirm', 'order_cancel']:
                model_id = self.env['ir.model'].search(
                    [('model', '=', 'sale.order')])
                self.model_id = model_id.id if model_id else False
            elif self.condition in ['order_delivered']:
                model_id = self.env['ir.model'].search(
                    [('model', '=', 'stock.picking')])
                self.model_id = model_id.id if model_id else False
            elif self.condition in ['invoice_vaildate', 'invoice_paid']:
                model_id = self.env['ir.model'].search(
                    [('model', '=', 'account.move')])
                self.model_id = model_id.id if model_id else False
        else:
            self.model_id = False

    @api.onchange('model_id')
    def onchange_model_id(self):
        if self.model_id:
            self.model = self.model_id.model
        else:
            self.model = False

    # @api.multi
    def get_body_data(self, obj, partner_id=None):
        self.ensure_one()
        if obj:
            body_msg = self.env["mail.template"].with_context(lang=partner_id.lang if partner_id else '').sudo()._render_template(
                self.sms_body_html, self.model, [obj.id])
            new_body_msg = re.sub("<.*?>", " ", body_msg[obj.id])
            return new_body_msg
            return " ".join(strip_tags(new_body_msg).split())

    @api.model
    def send_sms_using_template(self, mob_no, sms_tmpl, sms_gateway=None, obj=None):
        if not sms_gateway:

            gateway_id = self.env["sms.mail.server"].search(
                [], order='sequence asc', limit=1)
        else:
            gateway_id = sms_gateway
        if mob_no and sms_tmpl:
            sms_sms_obj = self.env["sms.sms"].create({
                'sms_gateway_config_id': gateway_id.id,
                'partner_id': obj.partner_id.id if obj else False,
                'to': mob_no,
                'group_type': 'individual',
                'auto_delete': sms_tmpl.auto_delete,
                'msg': sms_tmpl.get_body_data(obj, obj.partner_id) if obj else sms_tmpl.sms_body_html,
                'template_id': False
            })
            sms_sms_obj.send_sms_via_gateway(
                sms_sms_obj.msg, [sms_sms_obj.to], from_mob=None, sms_gateway=gateway_id)


    @api.model
    def send_sms_using_template_custom(self, ctx, mob_no, sms_tmpl, sms_gateway=None, obj=None ):
        if not sms_gateway:
            gateway = self.env["sms.smsclient"].search([])
        else:
            gateway = sms_gateway
        if gateway:
            # if not self._check_permissions():
            #     raise UserError(_('You have no permission to access %s') % (gateway.name,))
            url = gateway.url
            name = url
            if gateway.method == 'http':
                prms = {}
                for p in gateway.property_ids:
                    if p.type == 'user':
                        prms[p.name] = p.value
                    elif p.type == 'password':
                        prms[p.name] = p.value
                    elif p.type == 'to':
                        prms[p.name] = mob_no
                    elif p.type == 'sms':
                        prms[p.name] = gateway.text
                    elif p.type == 'extra':
                        prms[p.name] = p.value
                    elif p.type == 'type':
                        prms[p.name] = p.value
                    elif p.type == 'source':
                        prms[p.name] = p.value
                # prms['type'] = 0
                # prms['source'] = 'SD'
                prms['message'] = "Dear %s Your OTP Code is %s"%(ctx['name'],ctx['otp'],)
                prms['destination'] = mob_no[1:]

                params = parse.urlencode(prms)
                name = url + params
                # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=GMS&message=dfdf&destination=923136340004"
            # urlopen(
            # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=SD&message=newmessage&destination=923136340004")
            queue_obj = self.env['sms.smsclient.queue']
            vals = {
            'name': name,
            'gateway_id': gateway.id,
            'state': 'draft',
            'mobile': mob_no,
            'msg': prms['message'],
            # 'validity': data.validity,
            # 'classes': data.classes1,
            # 'deffered': data.deferred,
            # 'priorirty': data.priority,
            # 'coding': data.coding,
            # 'tag': data.tag,
            # 'nostop': data.nostop1,
        }
            queue_obj.create(vals)
            sms = self.env["sms.smsclient"]
            sms._check_queue()
        return True