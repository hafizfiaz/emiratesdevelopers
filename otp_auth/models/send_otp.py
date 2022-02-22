# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, models, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class SendOtp(models.TransientModel):
    _name = 'send.otp'
    _description = 'Send Otp'

    # @api.multi
    def email_send_otp(self, email, userName, otp):
        if not userName:
            userObj = self.env['res.users'].sudo().search([('login', '=', email)])
            userName = userObj.name
        uid = self.sudo()._uid
        templateObj = self.env.ref('otp_auth.email_template_edi_otp', raise_if_not_found=False)
        ctx = dict(templateObj._context or {})
        ctx['name'] = userName or 'User'
        ctx['otp'] = otp
        print(otp)
        values = templateObj.sudo().with_context(ctx).send_mail(uid, force_send=False,
                                                             raise_exception=False)
        mail = self.env['mail.mail'].sudo().search([('id','=',values)])
        server = self.env['ir.mail_server'].sudo().search([])

        if mail and server:
            mail.auto_delete = False
            mail.email_from = server[0].smtp_user
            mail.email_to = email
            mail.mail_server_id = server[0].id
            mail.send()

        # values = templateObj.sudo().with_context(ctx).send_mail(uid, force_send=True)
        # templateObj.send_mail(1, force_send=True)
        # values['email_to'] = email
        # mailObj = self.env['mail.mail'].sudo().with_context(ctx).create(values)
        # mailObj.sudo().send()
        return True
