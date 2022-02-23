# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, models, fields, _
from odoo.http import request
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

class Users(models.Model):
    _inherit = 'res.users'

    otp = fields.Boolean('OTP')

    @api.model
    def _check_credentials(self, password, user_agent_env):
        totp = request.session.get('otploginobj')
        print(totp)
        before = request.session.get('before')
        print("Before: "+str(before))
        print(self.sudo())
        isOTP = request.session.get('isOTP')
        user = self.sudo().search([('id', '=', self._uid)])
        if isOTP and not totp:
            print('rashidrashid')
            user = self.sudo().search([('id', '=', self._uid)])
            if user:
                self = user
                super(Users, self)._check_credentials(password, user_agent_env)
        if user and before == 0:
            if totp:
                print("totpVerify")
                print(password)

                verify = totp[1].verify(password)
                if verify:
                    print("Verify")
                    request.session['otpverified'] = True
                    user = self.sudo().search([('id', '=', self._uid)])
                    if not user:
                        raise AccessDenied()
                # else:
                #     raise AccessDenied()
                else:
                    request.session['otpverified'] = False
                    # password = str(password)+"12341"
                    if request.session.get('first_password') != 1:
                        password = password+"12312"
                    super(Users, self)._check_credentials(password, user_agent_env)
            else:
                super(Users, self)._check_credentials(password, user_agent_env)

        else:
            print("Else Verify iF passwor is correct")
            super(Users, self)._check_credentials(password, user_agent_env)
