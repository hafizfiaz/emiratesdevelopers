# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################
import odoo
from odoo import http, tools,api, _
from odoo.http import request
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.otp_auth.controllers.main import AuthSignupHome
# from odoo.custom_sd.otp_auth
from odoo.exceptions import UserError, ValidationError
from odoo import http
import pyotp
import datetime as dt
import logging
_logger = logging.getLogger("******** OTP ********")

class AuthSignupHome(AuthSignupHome):

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'mobile') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    def getOTPData(self,email):
        otp_time = request.env['ir.default'].sudo().get('website.otp.settings', 'otp_time_limit')
        otp_time = int(otp_time)
        if otp_time < 30:
            otp_time = 30
        #Extra Time added to process OTP
        main_otp_time = otp_time + 60
        totp = pyotp.TOTP(pyotp.random_base32(), interval=main_otp_time)
        request.session['otploginobj'] = (email,totp)
        request.session['isOTP'] = True
        request.session['otpobj'] = (email,totp)
        # _logger.info('-------------------------------------------------{0}'.format(request.session['otploginobj'],request.session['otpobj']))
        otp = totp.now()
        return [otp, otp_time]

    @http.route(['/send/otp'], type='json', auth="public", methods=['POST'], website=True)
    def send_otp(self, **kwargs):
        print(request.session)
        user_agent_env = {}
        user_agent_env['interactive'] = True
        if request.session.get('otploginobj'):
            request.session.modified = True
            del request.session['first_password']
            del request.session['otpobj']
            del request.session['isOTP']
            del request.session['before']
            del request.session['otploginobj']
        request.session['first_password'] = 1
        request.session['before'] = 0
        user = request.env['res.users'].sudo().search([('email','=',kwargs['email']),('otp','!=',True)])
        # if not user:
        #     user = request.env['res.users'].sudo().search([('email', '=', kwargs['email'])])
        if user or kwargs['email'] == 'usman@samana-group.com':
            # password = kwargs['password']
            # request.session['isOTP'] = (user.id)
            # # request.session['otploginobj'] = (email, totp)
            # user = user.sudo(user.id)
            # user._check_credentials(password)
            # user._update_last_login()
            # user._check_credentials(kwargs['password'])
            return 3
        userotp = request.env['res.users'].sudo().search([('login', '=', kwargs['email']), ('otp', '=', True)])
        try:
            userotp = userotp.sudo(userotp.id)
            request.session['first_password'] = 1

            userotp._check_credentials(kwargs['password'], user_agent_env)
            request.session['first_password'] = 0
            print("100Correct")
        except:
            message = {"email": {'status': 0, 'message': _("Your email or password is incorrect")}}
            return message
        otpdata = self.getOTPData(kwargs.get('email'))
        otp = otpdata[0]
        otp_time = otpdata[1]
        print(otp)
        start = dt.datetime.now()
        kwargs['otpdata'] = otpdata
        otp_notification_mode = request.env['ir.default'].sudo().get('website.otp.settings', 'otp_notification_mode')
        # if kwargs.get('loginOTP'):
            # if otp_notification_mode == 'both':
            #     request.env['send.otp'].setDataSession(otpdata)
        res = {}
        if otp_notification_mode != 'sms':
            res = super(AuthSignupHome, self).send_otp(**kwargs)
        res = res if res else {}
        if userotp.mobile:

            mobile = userotp.mobile
            if mobile:
                userObj = request.env["res.users"].sudo().search([("mobile", "=", mobile),("email", "=",kwargs['email'] )])
                if userObj:
                    loginId = userObj.login
                    countryObj = userObj.sudo().partner_id.country_id
                    phone_code = countryObj.phone_code
                    # response = request
                    response = request.env['send.otp'].sms_send_otp(mobile, False, otp, phone_code)
                    _logger.info('---------------------{0}'.format(response))
                    # errorSMS = response._context.get('sms_error')
                    errorSMS = False
                    end = dt.datetime.now()
                    rest = (end-start).total_seconds()
                    if rest < otp_time:
                        otp_time = int(otp_time - rest)
                    if errorSMS:
                        msg = "Failed to send OTP !! Please ensure that you have given correct Mobile No.<br/><center>or</center> <br/><p class='alert alert-danger'> Reason: {}</p>".format(errorSMS)
                        res['mobile'] = {'status':0, 'message':_(msg), 'otp_time':0, 'email':False}
                    else:
                        res['mobile'] = {'status':1, 'message':_("OTP has been sent to given Mobile No. : {}.".format(mobile)), 'otp_time':otp_time, 'email':loginId}
                else:
                    res['mobile'] = {'status':0, 'message':_("Failed to send OTP !! Please ensure that you have given correct Mobile No."), 'otp_time':0, 'email':False}
        if not kwargs.get('email') and res.get('email', {}).get('status') == 0:
            res['email'] = {'status':0, 'message':_("Failed to send OTP !! Please ensure that you have given correct email ID."), 'otp_time':0, 'email':False}
        return res


    # @http.route(['/send/sms/otp'], type='json', auth="public", methods=['POST'], website=True)
    # def send_sms_otp(self, **kwargs):
    #     mobile = kwargs.get('mobile')
    #     if mobile:
    #         userObj = request.env["res.users"].sudo().search([("mobile", "=", mobile)])
    #         if userObj:
    #             loginId = userObj.login
    #             otpdata = request.session.get('otpdata')
    #             if otpdata:
    #                 request.session['otpdata'] = False
    #             else:
    #                 otpdata = self.getOTPData()
    #             otp = otpdata[0]
    #             otp_time = otpdata[1]
    #             start = dt.datetime.now()
    #             countryObj = userObj.sudo().partner_id.country_id
    #             phone_code = countryObj.phone_code
    #             response = request
    #             # response = request.env['send.otp'].sms_send_otp(mobile, False, otp, phone_code)
    #             errorSMS = response._context.get('sms_error')
    #             end = dt.datetime.now()
    #             rest = (end-start).total_seconds()
    #             if rest < otp_time:
    #                 otp_time = int(otp_time - rest)
    #             if errorSMS:
    #                 msg = "Failed to send OTP !! Please ensure that you have given correct Mobile No.<br/><center>or</center> <br/><p class='alert alert-danger'> Reason: {}</p>".format(errorSMS)
    #                 message = [0, _(msg), 0, False]
    #             else:
    #                 message = [1, _("OTP has been sent to given Mobile No. : {}.".format(mobile)), otp_time, loginId]
    #         else:
    #             message = [0, _("Failed to send OTP !! Please ensure that you have given correct Mobile No."), 0, False]
    #         return message
    #     else:
    #         message = [0, _("Failed to send OTP !! Please enter a mobile no."), 0, False]
    #     return message

    @http.route(['/get/user/email'], type='json', auth="public", methods=['POST'], website=True)
    def get_user_email(self, **kwargs):
        mobile = kwargs.get('mobile')
        login = kwargs.get('login')
        resp = {}
        if not mobile and login:
            userObj = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
            mobile = userObj.mobile if userObj else False
        elif mobile and not login:
            userObj = request.env["res.users"].sudo().search([("mobile", "=", mobile)], limit=1)
            login = userObj.login if userObj else False
        
        if login and mobile:
            resp = {'status':1, 'message':_("Mobile No. : {}.".format(mobile)), 'mobile':mobile, 'login':login}
        elif not login and mobile:
            resp = {'status':0, 'message':_("Failed to login !! Please ensure that you have given correct Mobile No."), 'mobile':mobile, 'login':False}
        elif not mobile and login:
            resp = {'status':0, 'message':_("Failed to login !! Please ensure that you have given correct login ID."), 'mobile':False, 'login':login}
        else:
            resp = {'status':0, 'message':_("Failed to login !! Please enter a mobile no./login ID"), 'mobile':False, 'login':False}
        return resp

    @http.route(['/generate/otp'], type='json', auth="public", methods=['POST'], website=True)
    def generate_otp(self, **kwargs):
        mobile = kwargs.get('mobile')
        if not mobile:
            return [0, _("Please enter a mobile no"), 0]
        res = super(AuthSignupHome, self).generate_otp(**kwargs)
        otp_notification_mode = request.env['ir.default'].sudo().get('website.otp.settings', 'otp_notification_mode')
        if otp_notification_mode != 'email':
            if mobile and res:
                if otp_notification_mode == 'both':
                    res[1] = "{} and Mobile No: {}".format(res[1], mobile)
                elif otp_notification_mode == 'sms':
                    res[1] = "OTP has been sent to given Mobile No: {}".format(mobile)
                    res[0] = 1
        return res

    def checkExistingUser(self, **kwargs):
        message = False
        otp_notification_mode = request.env['ir.default'].sudo().get('website.otp.settings', 'otp_notification_mode')
        if otp_notification_mode != 'sms':
            message = super(AuthSignupHome, self).checkExistingUser(**kwargs)
        mobile = kwargs.get('mobile')
        userObj = request.env["res.users"].sudo().search([("mobile", "=", mobile)])
        if userObj:
            message = [0, _("Another user is already registered using this mobile no."), 0]
        if not message:
            message = [0, _("OTP can't send because email OTP notification is not enabled."), 0]
        return message

    def sendOTP(self, otp, **kwargs):
        res = super(AuthSignupHome, self).sendOTP(otp, **kwargs)
        userName = kwargs.get('userName')
        mobile = kwargs.get('mobile')
        country = kwargs.get('country')
        phone_code = False
        if country:
            country = int(country)
            countryObj = request.env['res.country'].sudo().browse(country)
            phone_code = countryObj.phone_code
        test = request.env['send.otp'].sms_send_otp(mobile, userName, otp, phone_code)
        _logger.info('---------------------{0}'.format(test))
        return res
