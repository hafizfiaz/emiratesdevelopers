# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from odoo.tools.translate import _
import logging
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)
from odoo import api, models
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta


class ProductCatalogueReport(models.AbstractModel):
    """ Model to contain the information related to printing the information about
    the products"""

    _name = "report.property_website.report_website_template"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the report values.
                        :param : model
                        :param : docids
                        :param : data
                        :return : data
                        :return : Product template records"""
        payment_schedule_id = docids[0]
        property_id = docids[1]
        payments = self.env['payment.schedule'].browse(payment_schedule_id)
        all_dates = []
        payment_date = date.today()
        all_dates.append(payment_date)

        for line in payments.payment_criteria_ids:
            a = 0
            while a < line.no_of_period:
                payment_date = payment_date+relativedelta(months=1)
                all_dates.append(payment_date)
                a+=1
        property = self.env['account.asset.asset'].browse(property_id)
        return {
            'data': data,
            'docs': property,
            'payment': payments,
            'all_dates': all_dates,
        }

class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'
    _description = 'Asset'


    def date_pre_post(self, start_date,handover_date):
        if start_date and handover_date:
            try:
                start_date = start_date.date()
                handover_date = handover_date
                print(start_date)
                print(handover_date)
                if start_date <= handover_date:
                    print("pre completeion")
                    return "Pre Completetion"
                else:
                    print("post completeion")
                    return "Post Handover"
            except:
                if start_date <= handover_date:
                    print("pre1 completeion")
                    return "Pre Completetion"
                else:
                    print("post1 completeion")
                    return "Post Handover"

    # @api.multi
    # @api.onchange('type_id')
    # def comp_property_type(self):
    #     asset_id = self.env['account.asset.asset'].search(
    #         [('type_id','=',self.type_id.id),
    #         ('state','=','draft')])
    #     # property_id = self.env['property.suggested'].search([('property_id','=',self.id)])
    #     # # self.suggested_property_ids = asset_id.ids
    #     # print("property_id-----------", property_id)
    #     if asset_id:
    #         self.write({'suggested_property_ids':[(6, 0, [asset_id.ids])]})
    #         # self.suggested_property_ids.write({'other_property_id':  [(6, 0, [asset_id.ids])], 'property_id': self.id})
    #         print("asset_id------------>", asset_id)

    # suggested_property_ids = fields.One2maan
    suggested_property_ids = fields.Many2many(
        'property.suggested','rel_suggested_property', 'property_id', 'suggested_id', 'Suggested Properties')
    # suggested_property_ids = fields.One2many(
    #     'property.suggested',
    #     'property_id',
    #     )
    cover_photos = fields.Binary(
        string='Cover Photos')
    menu_visible = fields.Boolean(
        string='Menu Visible')
    web_view_booking = fields.Boolean(string='Web View Booking Creation')
    menu_name = fields.Text(
        string='Menu Name')
    menu_url = fields.Char(
        string='Menu Url')
    arabic_project = fields.Char(string="Arabic Project Name", track_visibility='onchange')
    arabic_plot_no = fields.Char(tring="Arabic Plot No", track_visibility='onchange')


    # @api.multi
    # @api.onchange('type_id')
    # def onchange_type_id(self):
    #     """
    #     """
    #     asset_id = self.env['account.asset.asset']

    #     if self.type_id:
    #         print('------IN----------')
    #         for asset in asset_id.search(
    #             [('type_id', '=', self.type_id.id)]):
    #             print("asset====>", asset)
    #             vals = {'other_property_id': asset.id,
    #             'property_id':self.id
    #             }
                
        # if self.type_id:
            # self.suggested_property_ids = [(6, 0, [rec.id for rec in asset_id.search(
                # [('type_id', '=', self.type_id.id)])])]
            # print('self.suggested_property_ids-------->', self.suggested_property_ids)
            # self.employee_id = self.name.manager_id and \
            #     self.name.manager_id.id or False
    # @api.model
    # def create(self, vals):
    #     res = super(account_asset_asset, self).create(vals)
    #     if not res.suggested_property_ids and vals.get('suggested_property_ids'):
    #         line = [rec[1] for rec in vals.get('suggested_property_ids') if rec[1]]
    #         res.suggested_property_ids = [(6, 0, line)]
    #     return res

    # @api.multi
    # def write(self, vals):
    #     res = super(account_asset_asset, self).write(vals)
    #     if res:
    #         for rec in self:
    #             if not rec.suggested_property_ids and vals.get('suggested_property_ids'):
    #                 line = [mbr[1] for mbr in vals.get('suggested_property_ids') if mbr[1]]
    #                 for usr in line:
    #                     self._cr.execute(
    #                         "insert into rel_suggested_property \
    #                         (property_id,suggested_id) \
    #                      values(%s,%s)", (rec.id, usr))
    #     return res



    # @api.multi
    def _check_secondary_photo(self):
        account_assets_obj = self
        property_photo_true = []
        for one_photo_obj in account_assets_obj.property_photo_ids:
            one_property_photo_obj_true = one_photo_obj.secondary_photo
            property_photo_true.append(one_property_photo_obj_true)
        if property_photo_true.count(True) > 1:
            return False
        return True

    # _constraints = [
    #     (_check_secondary_photo, 'Error!\nSecondary photo is filled if you are change photo please remove first one.', [
    #         'property_photo_ids']),
    # ]


class property_suggested(models.Model):
    _name = "property.suggested"

    other_property_id = fields.Many2one('account.asset.asset', 'Property')
    property_id = fields.Many2one('account.asset.asset', 'Property_1')


class AccountAsset(models.Model):
    _inherit = "account.asset.asset"

    completion_date = fields.Char('Completion Date', tracking=True)
    estimated_charge = fields.Char('Estimated Service Charge', tracking=True)
    floor_plan_image = fields.Binary('Floor Plan', tracking=True)
    site_plan = fields.Binary('Site Plan', tracking=True)
    unit_layout_image = fields.Binary('Unit Layout', tracking=True)
    ex_completion_date = fields.Date(string='Expected Completion Date')
    web_state = fields.Selection(([('draft','Available'),('sold','Sold')]),string='Web Status')

    @api.onchange('state')
    def _onchange_web_state(self):
        if self.state  == 'draft':
            self.web_state = 'draft'
        else:
            self.web_state = 'sold'

    @api.model
    def _update_web_status(self):
        properties = self.env['account.asset.asset'].search([('parent_id.name','=','Samana Hills')])
        a = 1
        for property in properties:
            if property.state == 'draft':
                property.web_state = 'draft'
            else:
                property.web_state = 'sold'
            print (a)
            a += 1


class property_photo(models.Model):
    _inherit = "property.photo"

    secondary_photo = fields.Boolean(
        'Secondary Photo', help='Show photo on website Hover.')


class TxPaypal(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _paypal_form_get_tx_from_data(self, data):
        reference, txn_id = data.get(
            'new_transaction_name'), data.get('txn_id')
        if not reference or not txn_id:
            error_msg = _('Paypal: received data with missing reference (%s) or txn_id (%s)') % (
                reference, txn_id)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].search(
            [('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'Paypal: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return self.browse(txs[0])
