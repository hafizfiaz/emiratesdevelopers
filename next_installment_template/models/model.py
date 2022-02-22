# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.translate import _
import time
from odoo.exceptions import UserError,Warning, ValidationError
from odoo import http
from urllib import parse
from googletrans import Translator
import base64
import io




class MailRecipients(models.Model):
    _inherit = "fgr.details"

    @api.model
    def send_fgr_payment_due_email(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'FGR Payment Due Alerts Recipients')])
        fgr_details = self.env['fgr.details'].search([('state', '=', 'confirm')])
        for rec in mr:
            if rec.user_ids:
                for line in fgr_details:
                    if line.Due_date:
                        current_date = datetime.now().date()
                        dates_diff = line.Due_date - current_date
                        days = dates_diff.days
                        if days in [1, 3]:
                            # if line.id in [104, 105]:
                            email_template = rec.env.ref('next_installment_template.fgr_payment_due_email')
                            if email_template.mail_server_id:
                                email_template.email_from = email_template.mail_server_id.name
                            email_template.email_to = rec.get_partner_ids(rec.user_ids)
                            email_template.send_mail(line.id, force_send=True)


class MailInherit(models.Model):
    _inherit = "mail.recipients"

    @api.model
    def send_spa_email(self):
        email = self.env['mail.recipients'].search(
            [('name', '=', 'Booking Cancellation/ SPA Termination')])
        for rec in email:
            spa = (self.env['sale.order'].search([('receipts_perc', '<=', 10),('is_cancelled', '=', False),('asset_project_id', '!=', False),
                                                  ('property_id', '!=', False),('days_difference', '>=', 40),
                                                  ('state', '!=',
                                                   ('cancel', 'refund_cancellation'))]))
            for recs in spa:
                booking_approved = self.env.ref('next_installment_template.spa_payment_perc_id')
                booking_approved.email_to = rec.get_partner_ids(rec.user_ids)
                booking_approved.send_mail(recs.id, force_send=True)
                recs.roll_back_state = recs.state
                recs.is_cancelled = True
                recs.write({'state': 'under_spa_termination'})

    @api.model
    def send_crm_emails(self):
        email = self.env['mail.recipients'].search(
            [('name', '=', 'Booking Cancellation/ SPA Termination')])
        for rec in email:
            crm = (self.env['crm.booking'].search([('type', '=', 'booking'),
                                                   ('is_buy', '=', True),
                                                   ('booking_days', '>=', 30),('is_cancelled', '=', False),
                                                   ('state', '!=', ('cancel', 'rejected', 'draft', 'approved'))]))
            for recs in crm:
                booking_approved = self.env.ref('next_installment_template.crm_under_cancellation_id')
                booking_approved.email_to = rec.get_partner_ids(rec.user_ids)
                booking_approved.send_mail(recs.id, force_send=True)
                recs.roll_back_state = recs.state
                recs.is_cancelled = True
                recs.write({'state': 'under_cancellation'})



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.model
    # def create(self, vals):
    #     res = super(SaleOrder, self).create(vals)
    #     self.send_spa_creation_email(res.id)
    #     return res

    # def action_is_buy_spa(self):
    #     self.write({'state': 'spa_draft'})
    #     # self.property_id.write({'state': 'book'})
    #     self.action_buy_create_spa()
    #     self.property_id.write({'state': 'sold'})
    #     self.send_spa_creation_email(self.id)

    def action_is_buy_spa(self):
        res = super(SaleOrder, self).action_is_buy_spa()
        self.send_spa_creation_email(self.id)
        return res

    def get_add_less_table(self, add_jv, less_jv):
        result_rec = []
        # total = 0
        if add_jv:
            for line in add_jv:
                result_rec.append({'jv_no': line.name, 'date': line.date, 'description': line.ref, 'amount': round(line.amount_total)})
                # inv_id = self.env['account.invoice'].search([('number','=', line.name)])
                # if inv_id:
                #     for inv_line in inv_id[0].invoice_line_ids:
                #         val_dict = {'jv_no': '', 'date': '', 'description': '', 'amount': 0}
                        # if inv_line.product_id:
                        #     val_dict['description'] = inv_line.product_id.name
                        # else:
                        #     val_dict['description'] = inv_line.name
                        # tax_total = 0
                        # if inv_line.invoice_line_tax_ids:
                        #     for tax_line in inv_line.invoice_line_tax_ids:
                        #         tax_total += (tax_line.amount / 100) * inv_line.price_subtotal
                        #
                        # res_amount = inv_line.price_subtotal + tax_total
                        # val_dict['amount'] = round(res_amount)
                        # result_rec.append(val_dict)
        if less_jv:
            for lline in less_jv:
                result_rec.append({'jv_no': lline.name, 'date': lline.date, 'description': lline.ref, 'amount': round(lline.amount_total) * (-1)})
        return result_rec


    def get_add_less_total(self, add_jv, less_jv):
        total = 0
        if add_jv:
            for line in add_jv:
                total+= round(line.amount_total)
        if less_jv:
            for lline in less_jv:
                total -= round(lline.amount_total)
        return total

    def get_approve_url(self,record):
        # action_id = record.env.ref('sale_rent_schedule_custom.action_sale_rent_mail')
        base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/approve_booking?id=' + str(
            record.id)
        # base_url = http.request.env['ir.config_parameter'].get_param('web.base.url') + '/web?id=' + str(
        #     record.id) + '&action=' + str(action_id.id) + '&' + 'model=' + record._name + '&' + 'view_type=form'
        return base_url


    def get_reject_url(self,record):
        # action_id = record.env.ref('sale_rent_schedule_custom.action_sale_rent_mail')
        base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/reject_booking?id=' + str(
            record.id)
        # base_url = http.request.env['ir.config_parameter'].get_param('web.base.url') + '/web?id=' + str(
        #     record.id) + '&action=' + str(action_id.id) + '&' + 'model=' + record._name + '&' + 'view_type=form'
        return base_url

    def action_tentative_booking(self):
        for rec in self:
            rec.state = 'tentative_booking'
            rec.tentative_booking_date = datetime.now().date()
            rec.send_tentative_booking_email()

    @api.model
    def send_booking_update_email(self, booking=False):
        if not self.id:
            res_id = booking
        else:
            res_id = self.id
        record = self.env['crm.booking'].search([('id', '=', res_id)])
        mr = self.env['mail.recipients'].search([('name', '=', 'Booking Update Recipients')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.booking_update_email')
                if record.date in ['review', 'confirm_spa', 'approved']:
                    closure_pdf1 = \
                    self.env.ref('sd_sale_order_report.report_closure_form').sudo()._render_qweb_pdf([res_id],
                                                                                                    data=None)[0]
                    closure_report = base64.b64encode(closure_pdf1)

                    report_name_closure = 'closure_form'
                    filename_closure = "%s.%s" % (report_name_closure, "pdf")
                    closure_form_attach = rec.env['ir.attachment'].create({
                        'name': filename_closure,
                        'datas': closure_report,
                        'store_fname': filename_closure,
                        'type': 'binary',
                    })

                    data = {}
                    data['schedule'] = False
                    data['context'] = {}
                    data['context']['active_ids'] = record.ids

                    reservation_pdf = \
                    self.env.ref('sd_sale_order_report.report_reservation_form').sudo()._render_qweb_pdf([res_id], data=data)[0]
                    reservation_report = base64.b64encode(reservation_pdf)

                    report_name_reservation = 'reservation_form'
                    filename_reservation = "%s.%s" % (report_name_reservation, "pdf")
                    reservation_form_attach = rec.env['ir.attachment'].create({
                        'name': filename_reservation,
                        'datas': reservation_report,
                        'store_fname': filename_reservation,
                        'type': 'binary',
                    })
                    email_template.attachment_ids = [(6, 0, [closure_form_attach.id, reservation_form_attach.id])]
                else:
                    email_template.attachment_ids = False

                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.send_mail(res_id, force_send=True)


    def send_tentative_booking_cancellation_email(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'Tentative Booking Cancellation Recipients')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.tentative_booking_email')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.send_mail(self.id, force_send=True)

    @api.model
    def send_booking_cancellation_alert(self):
        cb = self.env['sale.order'].search([('state', '=', 'tentative_booking')])
        for rec in cb:
            current_date = datetime.now().date()
            diff = current_date - rec.booking_date.date()
            rec.days = diff.days
            total_receipt_amount = (rec.asset_project_id.min_received_amount / 100) * rec.price
            if rec.asset_project_id.booking_expire_days and rec.total_receipts < total_receipt_amount:
                if diff.days == rec.asset_project_id.booking_expire_days - 7:
                    rec.send_tentative_booking_cancellation_email()
                if diff.days == rec.asset_project_id.booking_expire_days - 4:
                    rec.send_tentative_booking_cancellation_email()
                if diff.days > rec.asset_project_id.booking_expire_days:
                    rec.action_is_buy_canceled()

    def send_tentative_booking_email(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'Tentative Booking Recipients')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.tentative_booking_email')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name

                closure_pdf1 = self.env.ref('sd_sale_order_report.report_closure_form').sudo()._render_qweb_pdf([self.id], data=None)[0]
                closure_report = base64.b64encode(closure_pdf1)

                report_name_closure = 'closure_form'
                filename_closure = "%s.%s" % (report_name_closure, "pdf")
                closure_form_attach = rec.env['ir.attachment'].create({
                    'name': filename_closure,
                    'datas': closure_report,
                    'store_fname': filename_closure,
                    'type': 'binary',
                })

                data = {}
                data['schedule'] = True
                data['context']= {}
                data['context']['active_ids'] = self.ids

                reservation_pdf = self.env.ref('sd_sale_order_report.report_reservation_form').sudo()._render_qweb_pdf([self.id], data=data)[0]
                reservation_report = base64.b64encode(reservation_pdf)

                report_name_reservation = 'reservation_form_with_schedule'
                filename_reservation = "%s.%s" % (report_name_reservation, "pdf")
                reservation_form_attach = rec.env['ir.attachment'].create({
                    'name': filename_reservation,
                    'datas': reservation_report,
                    'store_fname': filename_reservation,
                    'type': 'binary',
                })

                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.attachment_ids = [(6, 0, [closure_form_attach.id,reservation_form_attach.id])]
                email_template.send_mail(self.id, force_send=True)

    def get_partner_ids(self, user_ids):
        if user_ids:
            anb = str([user.partner_id.email for user in user_ids]).replace('[', '').replace(']', '')
            return anb.replace("'", '')

    def send_booking_discount_approval_email(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'Booking Discount Approval')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.booking_discount_approval_email')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.send_mail(self.id, force_send=True)


    def send_spa_creation_email(self, so=False):
        if not self.id:
            res_id = so
        else:
            res_id = self.id
        mr = self.env['mail.recipients'].search([('name', '=', 'SPA Creation')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.spa_creation_email_template')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name
                so = self.env['sale.order'].search([('id', '=', res_id)])
                data = {}
                data['english'] = True
                data['context'] = {}
                data['context']['active_ids'] = [res_id]
                so.onchange_asset_project_id()
                if so:
                    so[0].sale_term_id = so[0].sale_term_id.id

                if so.asset_project_id.name in ['Samana Golf Avenue','Samana Park Views']:
                    spa_pdf = \
                    self.env.ref('spa_customizations.report_golf_form').sudo()._render_qweb_pdf([res_id], data=data)[0]
                else:
                    spa_pdf = \
                    self.env.ref('spa_customizations.report_sale_form').sudo()._render_qweb_pdf([res_id], data=data)[0]
                spa_report = base64.b64encode(spa_pdf)

                report_name_spa = 'spa_form'
                filename_spa = "%s.%s" % (report_name_spa, "pdf")
                spa_form_attach = rec.env['ir.attachment'].create({
                    'name': filename_spa,
                    'datas': spa_report,
                    'store_fname': filename_spa,
                    'type': 'binary',
                })
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.attachment_ids = [
                    (6, 0, [spa_form_attach.id])]
                email_template.send_mail(res_id, force_send=True)

        recipnts = self.env['mail.recipients'].search([('name', '=', 'Deal Closed')])
        for rec in recipnts:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.deal_closed_email_template')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name
                so = self.env['sale.order'].search([('id', '=', res_id)])
                data = {}
                data['schedule'] = False
                data['context'] = {}
                data['context']['active_ids'] = [so.id]

                reservation_pdf = \
                    self.env.ref('sd_sale_order_report.report_reservation_form').sudo()._render_qweb_pdf([so.id],
                                                                                                 data=data)[0]
                reservation_report = base64.b64encode(reservation_pdf)

                report_name_reservation = 'reservation_form'
                filename_reservation = "%s.%s" % (report_name_reservation, "pdf")
                reservation_form_attach = rec.env['ir.attachment'].create({
                    'name': filename_reservation,
                    'datas': reservation_report,
                    'store_fname': filename_reservation,
                    'type': 'binary',
                })
                closure_pdf1 = \
                    self.env.ref('sd_sale_order_report.report_closure_form').sudo()._render_qweb_pdf([so.id],
                                                                                                    data=None)[
                        0]
                closure_report = base64.b64encode(closure_pdf1)

                report_name_closure = 'closure_form'
                filename_closure = "%s.%s" % (report_name_closure, "pdf")
                closure_form_attach = rec.env['ir.attachment'].create({
                    'name': filename_closure,
                    'datas': closure_report,
                    'store_fname': filename_closure,
                    'type': 'binary',
                })
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.attachment_ids = [
                    (6, 0, [reservation_form_attach.id,closure_form_attach.id])]
                email_template.send_mail(res_id, force_send=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    back_dated_confirm = fields.Boolean('Back Dated Confirm', default=False)
    back_dated_cancel = fields.Boolean('Back Dated Cancel', default=False)

    # def rejected_check(self):
    #     res = super(AccountPayment, self).rejected_check()
    #     print("rejected_check")
    #     if self.amount > 0.0:  # and self.journal_id.subtype == 'receivable' and self.journal_id.type == 'cash':
    #         sms_env = self.env['partner.sms.send']
    #         data = self.env['sms.smsclient'].search([('name', '=', 'SAMANA')])
    #         # sender = self.env['res.users'].search(
    #         #     [('login', 'in', ['rashid@samana-group.com', 'rashid@samana-group.com', 'baig@globalmigration.co.uk'])])
    #         # print(sender)
    #         mr = self.env['mail.recipients'].search([('name', '=', 'Bounced Payment sms')])
    #         sender = mr.user_ids
    #         sms_list = []
    #         for rec in sender:
    #             if rec.mobile:
    #                 sms_list.append(rec.mobile)
    #         if self.partner_id.mobile:
    #             sms_list.append(rec.mobile)
    #         message = "Cheque Bounced" + "\nFrom: " + self.partner_id.name + "\nCheque No: " + self.check_number + "\nAmount: " + str(
    #             '{:,.2f}'.format(
    #                 self.amount)) + " AED" + "\nDate " + str(self.bounced_date.strftime('%d-%m-%Y'))
    #         print(message)
    #         for line in sms_list:
    #             if line:
    #                 if data:
    #                     # if not self._check_permissions():
    #                     #     raise UserError(_('You have no permission to access %s') % (data.name,))
    #                     url = data.url
    #                     name = url
    #                     if data.method == 'http':
    #                         prms = {}
    #                         for p in data.property_ids:
    #                             if p.type == 'user':
    #                                 prms[p.name] = p.value
    #                             elif p.type == 'password':
    #                                 prms[p.name] = p.value
    #                             elif p.type == 'to':
    #                                 prms[p.name] = line
    #                             elif p.type == 'sms':
    #                                 prms[p.name] = data.text
    #                             elif p.type == 'extra':
    #                                 prms[p.name] = p.value
    #                             elif p.type == 'type':
    #                                 prms[p.name] = p.value
    #                             elif p.type == 'source':
    #                                 prms[p.name] = p.value
    #                         # prms['type'] = 0
    #                         # prms['source'] = 'SD'
    #                         prms['message'] = message
    #                         prms['destination'] = line[1:]
    #
    #                         params = parse.urlencode(prms)
    #                         name = url + params
    #                         # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=GMS&message=dfdf&destination=923136340004"
    #                     # urlopen(
    #                     # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=SD&message=newmessage&destination=923136340004")
    #                     queue_obj = self.env['sms.smsclient.queue']
    #                     vals = {
    #                         'name': name,
    #                         'gateway_id': data.id,
    #                         'state': 'draft',
    #                         'mobile': line,
    #                         'msg': prms['message'],
    #                         # 'validity': data.validity,
    #                         # 'classes': data.classes1,
    #                         # 'deffered': data.deferred,
    #                         # 'priorirty': data.priority,
    #                         # 'coding': data.coding,
    #                         # 'tag': data.tag,
    #                         # 'nostop': data.nostop1,
    #                     }
    #                     send_sms = queue_obj.create(vals)
    #                     sms = self.env["sms.smsclient"]
    #                     sms._check_queue()
    #                 # print(partner_sms)
    #     return res
    # @api.multi
    # def action_draft_to_cancel(self):
    #     for line in self:
    #         if line.journal_id.type == 'pdc' and line.state in ['draft','under_approval','under_accounts_verification','approved','rejected']:
    #             line.write({'state': 'cancelled', 'state': 'cancelled'})
    #             self._onchange_partner_type()
    #         if line.journal_id.type != 'pdc' and line.state in ['draft','under_approval','under_accounts_verification','approved','rejected']:
    #             line.write({'state': 'cancelled', 'state': 'cancelled'})

    @api.model
    def send_back_dated_receipt_cancel_email(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'Back Dated Receipts Recipients')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.receipt_Back_dated_receipt_cancellation_email')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.send_mail(self.id, force_send=True)

    @api.model
    def send_back_dated_receipt_confirm_email(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'Back Dated Receipts Recipients')])
        for rec in mr:
            if rec.user_ids:
                email_template = rec.env.ref('next_installment_template.receipt_Back_dated_receipt_email')
                if email_template.mail_server_id:
                    email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.send_mail(self.id, force_send=True)


    def action_draft_to_cancel(self):
        res = super(AccountPayment, self).action_draft_to_cancel()
        for line in self:
            if line.journal_id.type == 'pdc' and line.state in ['draft','under_approval','under_accounts_verification','approved','rejected']:
                line.write({'state': 'cancelled'})

            if line.journal_id.type != 'pdc' and line.state in ['draft','under_approval','under_accounts_verification','approved','rejected']:
                line.write({'state': 'cancelled'})
            current_date = datetime.now().date()
            if current_date > self.date:
                if not self.back_dated_cancel and self.payment_type == 'inbound':
                    self.send_back_dated_receipt_cancel_email()
                    self.back_dated_cancel = True


    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()
        current_date = datetime.now().date()
        if current_date > self.date:
            if not self.back_dated_cancel and self.payment_type == 'inbound':
                self.send_back_dated_receipt_cancel_email()
                self.back_dated_cancel = True
        return res

    def submit_accounts_verification(self):
        res = super(AccountPayment, self).submit_accounts_verification()
        current_date = datetime.now().date()
        if current_date > self.date:
            if not self.back_dated_confirm and self.payment_type == 'inbound':
                self.send_back_dated_receipt_confirm_email()
                self.back_dated_confirm = True
        return res



class SaleRentSchedule(models.Model):
    _inherit= "sale.rent.schedule"

    def get_url(self,record):
        # action_id = record.env.ref('sale_rent_schedule_custom.action_sale_rent_mail')
        base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/schedule/?id=' + str(
            record.id)
        # base_url = http.request.env['ir.config_parameter'].get_param('web.base.url') + '/web?id=' + str(
        #     record.id) + '&action=' + str(action_id.id) + '&' + 'model=' + record._name + '&' + 'view_type=form'
        return base_url

    def arabic_text(self, text):
        text = str(text)
        translator = Translator()
        try:
            value = translator.translate(text, dest="ar")
        except:
            return text
        return value.text

    @api.model
    def send_installment_email(self):
        srs = self.env['sale.rent.schedule'].search([('state', '=', 'confirm'),('sale_id.state','=','sale')])
        for rec in srs:
            sale = rec.sale_id
            if sale.state not in ['refund_cancellation','cancel'] and round(sale.receipts_perc) < 100 and round(sale.total_receipts) <= round(sale.balance_due_collection) and round(sale.instalmnt_bls_pend_plus_admin_oqood) > round(sale.matured_pdcs):
                if rec.start_date:
                    current_date = datetime.now().date()
                    st_date = rec.start_date
                    dates_diff = rec.start_date - current_date
                    days = dates_diff.days

                    terminations = self.env['termination.process'].search([])
                    stage_ids = self.env['project.stage'].search([('name', '=', 'New Termination Request')])
                    cancel_stage_id = self.env['project.stage'].search([('name', '=', 'Termination Cancel & Sorted')]).id
                    if days <= -90 and rec.pen_amt > 0:
                        already_exist = terminations.filtered(lambda a: a.stage_id.id != cancel_stage_id and a.spa.id == sale.id)
                        if not already_exist:
                            termination_id = self.env['termination.process'].create({
                                'subject': 'Termination - ' + str(sale.asset_project_id.name) + " " + str(sale.property_id.name),
                                'spa': sale.id,
                                'property': rec.property_id.id if rec.property_id else sale.property_id.id or False,
                                'project': rec.asset_property_id.id if rec.asset_property_id else sale.asset_project_id.id or False,
                                'stage_id': stage_ids.id if stage_ids else False,
                            })

                    # mr = self.env['mail.recipients'].search([('name','=','Courier Recipients')])
                    # for rec in mr:
                    #     if rec.user_ids:


                    if days in [0,7,15]:
                        penalty_pdf = \
                        rec.env.ref('sd_sale_order_report.report_sale_customer_penalty').sudo()._render_qweb_pdf(
                            [rec.sale_id.id], data=None)[0]
                        penalty_report = base64.b64encode(penalty_pdf)

                        report_name_penalty = 'customer_statement'
                        filename_penalty = "%s.%s" % (report_name_penalty, "pdf")
                        penalty_form_attach = rec.env['ir.attachment'].create({
                            'name': filename_penalty,
                            'datas': penalty_report,
                            'store_fname': filename_penalty,
                            'type': 'binary',
                        })
                        email_template = rec.env.ref('next_installment_template.email_next_installment')
                        # outgoing_server = rec.env['ir.mail_server'].search([('name','=','alert@samanadevelopers.com')])
                        if email_template.mail_server_id:
                            email_template.email_from = email_template.mail_server_id.name
                        email_template.attachment_ids = [(6, 0, [penalty_form_attach.id])]
                        # email_template.email_to = 'rashid@samana-group.com'
                        email_template.send_mail(rec.id, force_send=True)
                        # rec.env.cr.commit()

                    # if days in range(-7,0):
                    if days in [-7,-15,-30,-75]:
                        penalty_pdf = rec.env.ref('sd_sale_order_report.report_sale_customer_penalty').sudo()._render_qweb_pdf(
                            [rec.sale_id.id], data=None)[0]
                        penalty_report = base64.b64encode(penalty_pdf)

                        report_name_penalty = 'customer_statement'
                        filename_penalty = "%s.%s" % (report_name_penalty, "pdf")
                        penalty_form_attach = rec.env['ir.attachment'].create({
                            'name': filename_penalty,
                            'datas': penalty_report,
                            'store_fname': filename_penalty,
                            'type': 'binary',
                        })
                        if rec.pen_amt > 1000:
                            # email_template = rec.env.ref('next_installment_template.email_after_due_installment_15')
                            if days == -7:
                                email_template = rec.env.ref('next_installment_template.email_after_due_installment')
                            if days == -15:
                                email_template = rec.env.ref('next_installment_template.email_after_due_installment_15')
                            if days == -30:
                                email_template = rec.env.ref('next_installment_template.email_after_due_installment_15')
                            if days == -75:
                                email_template = rec.env.ref('next_installment_template.email_sg_developer_notice')
                                if email_template.mail_server_id:
                                    email_template.email_from = email_template.mail_server_id.name
                                # email_template.email_to = 'rashid@samana-group.com'
                                email_template.send_mail(rec.id, force_send=True)

                            # outgoing_server = rec.env['ir.mail_server'].search([('name','=','alert@samanadevelopers.com')])
                            else:
                                if email_template.mail_server_id:
                                    email_template.email_from = email_template.mail_server_id.name

                                email_template.attachment_ids = [(6, 0, [penalty_form_attach.id])]
                                # email_template.mail_server_id = outgoing_server.id
                                # email_template.email_to = 'rashid@samana-group.com'
                                email_template.send_mail(rec.id, force_send=True)# rec.env.cr.commit()

                        if rec.pen_amt > 0:
                            # email_template = rec.env.ref('next_installment_template.email_after_due_installment_15')
                            if days == -7:
                                email_template = rec.env.ref('next_installment_template.email_after_due_installment')
                            if days == -15:
                                email_template = rec.env.ref('next_installment_template.email_after_due_installment_15')
                            if days == -30:
                                email_template = rec.env.ref('next_installment_template.email_after_due_installment_15')
                            if days == -75:
                                email_template = rec.env.ref('next_installment_template.email_sg_developer_notice')
                                if email_template.mail_server_id:
                                    email_template.email_from = email_template.mail_server_id.name
                                # email_template.email_to = 'rashid@samana-group.com'
                                email_template.send_mail(rec.id, force_send=True)

                            # outgoing_server = rec.env['ir.mail_server'].search([('name','=','alert@samanadevelopers.com')])
                            else:
                                if email_template.mail_server_id:
                                    email_template.email_from = email_template.mail_server_id.name

                                email_template.attachment_ids = [(6, 0, [penalty_form_attach.id])]
                                # email_template.mail_server_id = outgoing_server.id
                                # email_template.email_to = 'rashid@samana-group.com'
                                email_template.send_mail(rec.id, force_send=True)# rec.env.cr.commit()

