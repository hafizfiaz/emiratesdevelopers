from odoo import tools
from odoo import models, fields, api
from googletrans import Translator
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import time


class ReportReservationForm(models.AbstractModel):
    _name = 'report.property_website.report_website_template_new'
    _description = 'Reservation Report'

    def arabic_text(self, text):
        if text:
            text = str(text)
            translator = Translator()
            try:
                vals = translator.translate(text, dest="ar")
            except:
                try:
                    vals = translator.translate(text, dest="ar")
                except:
                    return text
            # translator.translate(text, dest="ar")
            return vals.text
        else:
            return True

    def calculate_months(self, date):
        date1 = datetime.strptime(str(date), '%Y-%m-%d')
        date2 = datetime.strptime(datetime.strftime(datetime.now(), '%Y-%m-%d'),'%Y-%m-%d')
        r = relativedelta(date1, date2)
        return r.months+1 + (12*r.years)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset.asset'].search([('id', '=', docids[1])])
        payment = self.env['payment.schedule'].search([('id', '=', docids[0])])
        contact_name = 'None'
        contact_mobile = 'None'
        contact_email = 'None'
        if docs:
            new_date = date.today()
            print(new_date)
            list_rent = []
            last_line = 0
            c = 1
        total_payment = docs.value
        total_manual = 0
        percent_minus = 0
        all_loops = 0
        per = 0
        bb = 0
        list = []
        dictionary = {}
        new_date = date.today()
        for criteria in payment.payment_criteria_ids:

            if criteria.value == 'fixed' or criteria.value == 'percent' and criteria.amount_get == 'manual':
                if criteria.value_amount > 0:
                    # self.down_payment = criteria.value_amount
                    if criteria.value == 'percent':
                        percentage = criteria.value_amount
                        percent_minus += percentage
                        percent_value = percentage / 100 * total_payment
                        total_manual += percent_value

                        bb = percent_minus
                    else:
                        percent_value = criteria.value_amount
                        total_manual = criteria.value_amount
                        total_payment = total_payment - percent_value
                    if criteria.period == 'monthly':
                        new_date = new_date + relativedelta(months=1)
                    elif criteria.period == 'quarterly':
                        new_date = new_date + relativedelta(months=3)
                    elif criteria.period == 'bi_annulay':
                        new_date = new_date + relativedelta(months=6)
                    elif criteria.period == 'annual':
                        new_date = new_date + relativedelta(months=12)
                    elif criteria.period == 'no_of_days':
                        if date.today():
                            installment_date = date.today() + timedelta(
                                days=criteria.no_of_days)
                        else:
                            new_date = new_date + relativedelta(days=criteria.no_of_days)
                    elif criteria.period == 'custom_date':
                        new_date = criteria.custom_date
                    else:
                        raise UserError('Please select Period on Payment Schedule')
                    # total_payment = total_payment - percent_value
                    dictionary = {
                        'start_date':
                            installment_date if date.today() and criteria.period == 'no_of_days' else
                            new_date,
                        'amount_without_vat': percent_value,
                        'calculation': criteria.value,
                        'value': criteria.value_amount,
                        # 'vat_id': self.vat_id.id,
                        # 'sale_type': self.sale_type,
                        # 'partner_id': self.partner_id.id,
                        # 'property_id': self.property_id.id,
                        # 'asset_property_id': self.asset_project_id.id,
                    }
                    list.append(dictionary)
            payment_without_down = total_payment
            if criteria.value == 'percent' and criteria.amount_get == 'auto':
                a = criteria.value_amount
                count = (100 - percent_minus) % criteria.value_amount

                total_loop = (100 - percent_minus) / criteria.value_amount

                # total_payment = total_payment - total_manual
                if criteria.period in ['quarterly', 'monthly', 'bi_annulay', 'annual']:
                    if criteria.no_of_period > 0:
                        per = criteria.value_amount * criteria.no_of_period + per + bb
                        bb = 0
                        percent_minus = percent_minus + (criteria.value_amount * criteria.no_of_period)
                        # total_loop = (100 - percent_minus) / criteria.value_amount
                        total_loop = criteria.no_of_period

                        all_loops = all_loops + criteria.no_of_period
                        count = 0
                    if criteria.no_of_period == 0:
                        # all_loops = all_loops + criteria.no_of_period
                        total_loop = (100 - percent_minus) / criteria.value_amount

                        count = (100 - percent_minus) % criteria.value_amount
                        if not count.is_integer():
                            count = round(count, 2)

                if count > 0:
                    total_loop -= 2
                    last_line = count + criteria.value_amount
                    c = 0

                while total_loop >= c:
                    if count == 0:
                        percentage = criteria.value_amount
                        percent_value = percentage / (100) * total_payment
                        total_loop = total_loop - 1
                        if criteria.period == 'monthly':
                            new_date = new_date + relativedelta(months=1)
                        elif criteria.period == 'quarterly':
                            new_date = new_date + relativedelta(months=3)
                        elif criteria.period == 'bi_annulay':
                            new_date = new_date + relativedelta(months=6)
                        elif criteria.period == 'annual':
                            new_date = new_date + relativedelta(months=12)
                        elif criteria.period == 'no_of_days':
                            if date.today():
                                installment_date = date.today() + timedelta(
                                    days=criteria.no_of_days)
                            else:
                                new_date = new_date + relativedelta(days=criteria.no_of_days)
                        elif criteria.period == 'custom_date':
                            new_date = criteria.custom_date
                        else:
                            raise UserError('Please select Period on Payment Schedule')
                        # total_payment = total_payment - percent_value
                        dictionary = {
                            'start_date':
                                installment_date if date.today() and criteria.period == 'no_of_days' else
                                new_date,
                            'amount_without_vat': percent_value,
                            'calculation': criteria.value,
                            'value': criteria.value_amount,
                            # 'vat_id': self.vat_id.id,
                            # 'sale_type': self.sale_type,
                            # 'partner_id': self.partner_id.id,
                            # 'property_id': self.property_id.id,
                            # 'asset_property_id': self.asset_project_id.id,
                        }
                        list.append(dictionary)
                    if count > 0:
                        percentage = criteria.value_amount
                        percent_value = percentage / 100 * total_payment
                        total_loop = total_loop - 1
                        if criteria.period == 'monthly':
                            new_date = new_date + relativedelta(months=1)
                        elif criteria.period == 'quarterly':
                            new_date = new_date + relativedelta(months=3)
                        elif criteria.period == 'bi_annulay':
                            new_date = new_date + relativedelta(months=6)
                        elif criteria.period == 'annual':
                            new_date = new_date + relativedelta(months=12)
                        elif criteria.period == 'no_of_days':
                            if date.today():
                                installment_date = date.today() + timedelta(
                                    days=criteria.no_of_days)
                            else:
                                new_date = new_date + relativedelta(days=criteria.no_of_days)
                        elif criteria.period == 'custom_date':
                            new_date = criteria.custom_date
                        else:
                            raise UserError('Please select Period on Payment Schedule')
                        # total_payment = total_payment - percent_value
                        dictionary = {
                            'start_date':
                                installment_date if date.today() and criteria.period == 'no_of_days' else
                                new_date,
                            'amount_without_vat': percent_value,
                            'calculation': criteria.value,
                            'value': criteria.value_amount,
                            # 'vat_id': self.vat_id.id,
                            # 'sale_type': self.sale_type,
                            # 'partner_id': self.partner_id.id,
                            # 'property_id': self.property_id.id,
                            # 'asset_property_id': self.asset_project_id.id,
                        }
                        list.append(dictionary)
                if last_line > criteria.value_amount:
                    percent_value = last_line / 100 * total_payment
                    if criteria.period == 'monthly':
                        new_date = new_date + relativedelta(months=1)
                    elif criteria.period == 'quarterly':
                        new_date = new_date + relativedelta(months=3)
                    elif criteria.period == 'bi_annulay':
                        new_date = new_date + relativedelta(months=6)
                    elif criteria.period == 'annual':
                        new_date = new_date + relativedelta(months=12)
                    elif criteria.period == 'no_of_days':
                        if date.today():
                            installment_date = date.today() + timedelta(
                                days=criteria.no_of_days)
                        else:
                            new_date = new_date + relativedelta(days=criteria.no_of_days)
                    elif criteria.period == 'custom_date':
                        new_date = criteria.custom_date
                    else:
                        raise UserError('Please select Period on Payment Schedule')
                    # total_payment = total_payment - percent_value
                    dictionary = {
                        'start_date':
                            installment_date if date.today() and criteria.period == 'no_of_days' else
                            new_date,
                        'amount_without_vat': percent_value,
                        'calculation': criteria.value,
                        'value': criteria.value_amount,
                        # 'vat_id': self.vat_id.id,
                        # 'sale_type': self.sale_type,
                        # 'partner_id': self.partner_id.id,
                        # 'property_id': self.property_id.id,
                        # 'asset_property_id': self.asset_project_id.id,
                    }
                    list.append(dictionary)
        handover_date = docs.parent_id.handover_date
        today = date.today()
        total_months = (handover_date.year - today.year) * 12 + (handover_date.month - today.month)
        print("Total Months " + str(total_months))
        print(handover_date)
        if len(docids) > 3:
            contact_name = docids[3]
        if len(docids) > 4:
            contact_mobile = docids[4]
        if len(docids) > 5:
            contact_email = docids[5]
        list = sorted(list, key=lambda v: str(v['start_date']))
        print(list)
        return {
            'calculate_months': self.calculate_months,
            'arabic_text': self.arabic_text,
            'doc_ids': docids,
            # 'doc_model': 'account.invoice',
            'docs': docs,
            'contact_name': contact_name,
            'contact_mobile': contact_mobile,
            'contact_email': contact_email,
            'payment': payment,
            'total_payment': total_payment,
            'list_a': list,
            'total_months': total_months,
            'start_date': today,
            'payment_selected': docids[2],
            'report_type': data.get('report_type') if data else '',
        }


class ReportReservationFormGolf(models.AbstractModel):
    _name = 'report.property_website.golf_report_website_template_new'
    _description = 'Reservation Report'


    def arabic_text(self, text):
        if text:
            text = str(text)
            translator = Translator()
            try:
                vals = translator.translate(text, dest="ar")
            except:
                try:
                    vals = translator.translate(text, dest="ar")
                except:
                    return text
            # translator.translate(text, dest="ar")
            return vals.text
        else:
            return True

    def calculate_months(self, date):
        date1 = datetime.strptime(str(date), '%Y-%m-%d')
        date2 = datetime.strptime(datetime.strftime(datetime.now(), '%Y-%m-%d'),'%Y-%m-%d')
        r = relativedelta(date1, date2)
        return r.months + (12*r.years)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset.asset'].search([('id','=',docids[1])])
        payment = self.env['payment.schedule'].search([('id','=',docids[0])])
        contact_name = 'None'
        contact_mobile = 'None'
        contact_email = 'None'
        if docs:
            new_date = date.today()
            print(new_date)
            list_rent = []
            last_line = 0
            c = 1
        total_payment = docs.value
        total_manual = 0
        percent_minus = 0
        all_loops = 0
        per = 0
        bb = 0
        list = []
        dictionary = {}
        new_date = date.today()
        for criteria in payment.payment_criteria_ids:

            if criteria.value == 'fixed' or criteria.value == 'percent' and criteria.amount_get == 'manual':
                if criteria.value_amount > 0:
                    # self.down_payment = criteria.value_amount
                    if criteria.value == 'percent':
                        percentage = criteria.value_amount
                        percent_minus += percentage
                        percent_value = percentage / 100 * total_payment
                        total_manual += percent_value

                        bb = percent_minus
                    else:
                        percent_value = criteria.value_amount
                        total_manual = criteria.value_amount
                        total_payment = total_payment - percent_value
                    if criteria.period == 'monthly':
                        new_date = new_date + relativedelta(months=1)
                    elif criteria.period == 'quarterly':
                        new_date = new_date + relativedelta(months=3)
                    elif criteria.period == 'bi_annulay':
                        new_date = new_date + relativedelta(months=6)
                    elif criteria.period == 'annual':
                        new_date = new_date + relativedelta(months=12)
                    elif criteria.period == 'no_of_days':
                        if date.today():
                            installment_date = date.today() + timedelta(
                                days=criteria.no_of_days)
                        else:
                            new_date = new_date + relativedelta(days=criteria.no_of_days)
                    elif criteria.period == 'custom_date':
                        new_date = criteria.custom_date
                    else:
                        raise UserError('Please select Period on Payment Schedule')
                    # total_payment = total_payment - percent_value
                    dictionary = {
                        'start_date':
                            installment_date if date.today() and criteria.period == 'no_of_days' else
                            new_date,
                        'amount_without_vat': percent_value,
                        'calculation': criteria.value,
                        'value': criteria.value_amount,
                        # 'vat_id': self.vat_id.id,
                        # 'sale_type': self.sale_type,
                        # 'partner_id': self.partner_id.id,
                        # 'property_id': self.property_id.id,
                        # 'asset_property_id': self.asset_project_id.id,
                    }
                    list.append(dictionary)
            payment_without_down = total_payment
            if criteria.value == 'percent' and criteria.amount_get == 'auto':
                a = criteria.value_amount
                count = (100 - percent_minus) % criteria.value_amount

                total_loop = (100 - percent_minus) / criteria.value_amount

                # total_payment = total_payment - total_manual
                if criteria.period in ['quarterly', 'monthly', 'bi_annulay', 'annual']:
                    if criteria.no_of_period > 0:
                        per = criteria.value_amount * criteria.no_of_period + per + bb
                        bb = 0
                        percent_minus = percent_minus + (criteria.value_amount * criteria.no_of_period)
                        # total_loop = (100 - percent_minus) / criteria.value_amount
                        total_loop = criteria.no_of_period

                        all_loops = all_loops + criteria.no_of_period
                        count = 0
                    if criteria.no_of_period == 0:
                        # all_loops = all_loops + criteria.no_of_period
                        total_loop = (100 - percent_minus) / criteria.value_amount

                        count = (100 - percent_minus) % criteria.value_amount
                        if not count.is_integer():
                            count = round(count, 2)

                if count > 0:
                    total_loop -= 2
                    last_line = count + criteria.value_amount
                    c = 0

                while total_loop >= c:
                    if count == 0:
                        percentage = criteria.value_amount
                        percent_value = percentage / (100) * total_payment
                        total_loop = total_loop - 1
                        if criteria.period == 'monthly':
                            new_date = new_date + relativedelta(months=1)
                        elif criteria.period == 'quarterly':
                            new_date = new_date + relativedelta(months=3)
                        elif criteria.period == 'bi_annulay':
                            new_date = new_date + relativedelta(months=6)
                        elif criteria.period == 'annual':
                            new_date = new_date + relativedelta(months=12)
                        elif criteria.period == 'no_of_days':
                            if date.today():
                                installment_date = date.today() + timedelta(
                                    days=criteria.no_of_days)
                            else:
                                new_date = new_date + relativedelta(days=criteria.no_of_days)
                        elif criteria.period == 'custom_date':
                            new_date = criteria.custom_date
                        else:
                            raise UserError('Please select Period on Payment Schedule')
                        # total_payment = total_payment - percent_value
                        dictionary = {
                            'start_date':
                                installment_date if date.today() and criteria.period == 'no_of_days' else
                                new_date,
                            'amount_without_vat': percent_value,
                            'calculation': criteria.value,
                            'value': criteria.value_amount,
                            # 'vat_id': self.vat_id.id,
                            # 'sale_type': self.sale_type,
                            # 'partner_id': self.partner_id.id,
                            # 'property_id': self.property_id.id,
                            # 'asset_property_id': self.asset_project_id.id,
                        }
                        list.append(dictionary)
                    if count > 0:
                        percentage = criteria.value_amount
                        percent_value = percentage / 100 * total_payment
                        total_loop = total_loop - 1
                        if criteria.period == 'monthly':
                            new_date = new_date + relativedelta(months=1)
                        elif criteria.period == 'quarterly':
                            new_date = new_date + relativedelta(months=3)
                        elif criteria.period == 'bi_annulay':
                            new_date = new_date + relativedelta(months=6)
                        elif criteria.period == 'annual':
                            new_date = new_date + relativedelta(months=12)
                        elif criteria.period == 'no_of_days':
                            if date.today():
                                installment_date = date.today() + timedelta(
                                    days=criteria.no_of_days)
                            else:
                                new_date = new_date + relativedelta(days=criteria.no_of_days)
                        elif criteria.period == 'custom_date':
                            new_date = criteria.custom_date
                        else:
                            raise UserError('Please select Period on Payment Schedule')
                        # total_payment = total_payment - percent_value
                        dictionary = {
                            'start_date':
                                installment_date if date.today() and criteria.period == 'no_of_days' else
                                new_date,
                            'amount_without_vat': percent_value,
                            'calculation': criteria.value,
                            'value': criteria.value_amount,
                            # 'vat_id': self.vat_id.id,
                            # 'sale_type': self.sale_type,
                            # 'partner_id': self.partner_id.id,
                            # 'property_id': self.property_id.id,
                            # 'asset_property_id': self.asset_project_id.id,
                        }
                        list.append(dictionary)
                if last_line > criteria.value_amount:
                    percent_value = last_line / 100 * total_payment
                    if criteria.period == 'monthly':
                        new_date = new_date + relativedelta(months=1)
                    elif criteria.period == 'quarterly':
                        new_date = new_date + relativedelta(months=3)
                    elif criteria.period == 'bi_annulay':
                        new_date = new_date + relativedelta(months=6)
                    elif criteria.period == 'annual':
                        new_date = new_date + relativedelta(months=12)
                    elif criteria.period == 'no_of_days':
                        if date.today():
                            installment_date = date.today() + timedelta(
                                days=criteria.no_of_days)
                        else:
                            new_date = new_date + relativedelta(days=criteria.no_of_days)
                    elif criteria.period == 'custom_date':
                        new_date = criteria.custom_date
                    else:
                        raise UserError('Please select Period on Payment Schedule')
                    # total_payment = total_payment - percent_value
                    dictionary = {
                        'start_date':
                            installment_date if date.today() and criteria.period == 'no_of_days' else
                            new_date,
                        'amount_without_vat': percent_value,
                        'calculation': criteria.value,
                        'value': criteria.value_amount,
                        # 'vat_id': self.vat_id.id,
                        # 'sale_type': self.sale_type,
                        # 'partner_id': self.partner_id.id,
                        # 'property_id': self.property_id.id,
                        # 'asset_property_id': self.asset_project_id.id,
                    }
                    list.append(dictionary)
        handover_date = docs.parent_id.handover_date
        today = date.today()
        total_months = (handover_date.year - today.year) * 12 + (handover_date.month - today.month)
        print("Total Monthsssss "+ str(total_months) )
        print(handover_date )
        if len(docids) > 3:
            contact_name = docids[3]
        if len(docids) > 4:
            contact_mobile = docids[4]
        if len(docids) > 5:
            contact_email = docids[5]
        list = sorted(list, key=lambda v: str(v['start_date']))
        return {
            'calculate_months': self.calculate_months,
            'arabic_text': self.arabic_text,
            'doc_ids': docids,
            # 'doc_model': 'account.invoice',
            'docs': docs,
            'contact_name': contact_name,
            'contact_mobile': contact_mobile,
            'contact_email': contact_email,
            'payment': payment,
            'total_payment': total_payment,
            'list_a': list,
            'total_months': total_months,
            'start_date': today,
            'payment_selected': docids[2],
            'report_type': data.get('report_type') if data else '',
        }

