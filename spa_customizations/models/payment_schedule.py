# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import time


class SaleOrderInherit(models.Model):
    _name = 'payment.schedule'
    _description = "Payment Schedule"

    state = fields.Selection(
        [('draft', 'Draft'), ('running', 'Running'),
         ('expired', 'Expired'),
         ('cancel', 'Cancel')],
        'Status', default='draft')
    name = fields.Char('Name',required=True)
    active = fields.Boolean('Active',default=True)

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset',string='Property')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    payment_criteria_ids = fields.One2many('payment.schedule.criteria','payment_schedule_id',string="Payment Schedule Criteria")
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    on_website = fields.Boolean('Show on Website')
    sale_type = fields.Selection([
        ('samana_sale', 'Samana Sale'),
        ('investor_sale', 'Investor Sale'),
    ], string='Sale Type', required=True, default='samana_sale')

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'), ('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    @api.onchange('payment_criteria_ids', 'payment_criteria_ids.value_amount')
    def get_calulated_percent(self):
        total_percentage = 0
        for record in self.payment_criteria_ids:
            if record.amount_get == 'manual' and record.value == 'percent':
                total_percentage += record.value_amount
        if total_percentage > 100:
            raise UserError('Manual Percentage is more than 100 Percent')
        print(total_percentage)

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date:
            if self.end_date <= datetime.datetime.now():
                self.state = 'expired'
            elif self.end_date > datetime.datetime.now() and self.state == 'expired':
                self.state = 'running'

    def get_expire_payment_schedule(self):
        """ Method that runs forever """
        all_data = self.env['payment.schedule'].search([])
        for data in all_data:
            if data.state:
                if data.end_date:
                    if data.end_date < datetime.datetime.now():
                        data.state = 'expired'
            else:
                data.state = 'draft'

    
    def draft_back(self):
        self.write({
            'state': 'draft',
        })

    
    def running(self):
        self.write({
            'state': 'running',
        })

    
    def expired(self):
        self.write({
            'state': 'expired',
        })

    
    def cancel(self):
        self.write({
            'state': 'cancel',
        })


class SaleOrderIznheritCriteria(models.Model):
    _name = 'payment.schedule.criteria'
    _description = "Payment Schedule Criteria"

    name = fields.Char('Sr.No')
    period = fields.Selection(
        [('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
         ('bi_annulay', 'Bi Annulay'),
         ('annual', 'Annual'),
         ('no_of_days', 'No of Days'),
         ('custom_date', 'Custom Date'),
         ],
        'Period')
    custom_date = fields.Datetime('Date')
    no_of_days = fields.Integer('No Of Days')

    payment_schedule_id = fields.Many2one('payment.schedule',string="Payment Schedule")

    value = fields.Selection([
        ('balance', 'Balance'),
        ('percent', 'Percent'),
        ('fixed', 'Fixed Amount')
    ], string='Type', required=True, default='balance',
        help="Select here the kind of valuation related to this payment terms line.")
    amount_get = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
    ], string='Payment Schedule Lines', required=True, default='auto',
        help="Select to generate Payment Lines on Manual or Automatic.")
    value_amount = fields.Float(string='Value')
    no_of_period = fields.Integer(string='No. of Period', default=0)
    days = fields.Integer(string='Number of Days', required=True, default=0)
    day_of_the_month = fields.Integer(string='Day of the month',
                                      help="Day of the month on which the invoice must come to its term. If zero or negative, this value will be ignored, and no specific day will be set. If greater than the last day of a month, this number will instead select the last day of this month.")
