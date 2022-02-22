# from openerp.osv import fields, orm, osv
from odoo import api, models, fields, _
import datetime
import calendar

class AssetAccount(models.Model):
    _inherit = 'account.asset.asset'

    # @api.multi
    def _compute_meeting_count_amendments(self):
        for data in self:
            data.meeting_count_amendment = len(data.env['sale.amendment'].search([('property_id', '=', data.id)]))

    meeting_count_amendment = fields.Integer('Sale Revert', compute='_compute_meeting_count_amendments', tracking=True)

    # @api.multi
    def button_sale_amendment(self):
        return {
            'name': _("Sale/Booking Amendment"),
            'view_mode': 'tree,form',
            'res_model': 'sale.amendment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.id)],
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.multi
    def _compute_meeting_count_amendments(self):
        for data in self:
            data.meeting_count_amendment = len(data.env['sale.amendment'].search([('spa_id', '=', data.id)]))


    amendment_id = fields.Many2one('sale.amendment', string="Sale Amendment", readonly=True)
    amendment_check = fields.Boolean('Sale Amendment', default=False, readonly=True)
    meeting_count_amendment = fields.Integer('Sale Revert', compute='_compute_meeting_count_amendments', tracking=True)

    def button_sale_amendment(self):
        ctx = {'default_spa_id': self.id}
        return {
            'name': _("Sale/Booking Amendment"),
            'view_id': self.env.ref('sale_amendment.view_sale_amendment_form').id,
            'view_mode': 'form',
            'context': ctx,
            'res_model': 'sale.amendment',
            'type': 'ir.actions.act_window'
        }


# class CrmBooking(models.Model):
#     _inherit = 'crm.booking'
#
#     # @api.multi
#     def _compute_meeting_count_amendments(self):
#         for data in self:
#             data.meeting_count_amendment = len(data.env['sale.amendment'].search([('spa_id', '=', data.id)]))
#
#     meeting_count_amendment = fields.Integer('Sale Revert', compute='_compute_meeting_count_amendments', tracking=True)
#
#     # @api.multi
#     def button_sale_amendment(self):
#         return {
#             'name': _("Sale/Booking Amendment"),
#             'view_type': 'form',
#             'view_mode': 'tree,form',
#             'res_model': 'sale.amendment',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#             'domain': [('spa_id', '=', self.id)],
#         }


class SaleAmendmentForm(models.Model):
    _name = 'sale.amendment'
    _description = "Sale Amendment"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    @api.depends('spa_id')
    # @api.multi# if these fields are changed, call method
    def _compute_changes(self):
        for data in self:
            data.asset_project_id = False
            data.property_id = False
            data.partner_id = False
            data.user_id = False
            data.mobile = False
            data.payment_schedule_id = False
            data.property_price_ex_vat = False
            if data.spa_id:
                # booking = self.env['crm.booking'].search(
                #     [('id', '=', data.spa_id.id)])
                sale = self.env['sale.order'].search(
                    [('id', '=', data.spa_id.id)])

                if data.spa_id:
                    # data.spa_id = booking[0].id or False
                    data.asset_project_id = data.spa_id.asset_project_id.id
                    data.property_id = data.spa_id.property_id.id
                    data.partner_id = data.spa_id.partner_id.id or False
                    data.user_id = data.spa_id.user_id.id or False
                    data.mobile = data.spa_id.partner_id.mobile or False
                    data.payment_schedule_id = data.spa_id.payment_schedule_id.id or False
                    data.property_price_ex_vat = data.spa_id.price or False

                if sale:
                    data.spa_id = sale[0].id or False


    @api.depends('spa_id')
    # @api.multi
    def _compute_amounts(self):
        for data in self:
            # data
            data.property_price_ex_vat = data.spa_id.price
            data.vat = data.spa_id.vat_amount
            data.property_price_inc_vat = data.spa_id.property_inc_vat_amount
            data.oqood_fee = data.spa_id.oqood_fee
            data.admin_fee = data.spa_id.admin_fee

    @api.depends('new_price','new_vat')
    # @api.multi
    def _compute_new_price(self):
        for data in self:
            data.new_property_price_inc_vat = data.new_price+data.new_vat

    @api.depends('spa_id')
    # @api.multi
    def _compute_receipts(self):
        for data in self:
            data.receipts_ids = False
            if data.spa_id:
                payments = self.env['account.payment'].search([('spa_id','=',data.spa_id.id),('state','!=','cancelled')])
                if payments:
                    data.receipts_ids = [[6, 0, payments.ids]]

    # @api.multi
    def amendment_print(self):

        return self.env.ref('sale_amendment.report_amendment_form').report_action(self, data=None)



    # name = fields.Char('Name')
    name = fields.Char('Serial Number', readonly=True, tracking=True)

    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]", compute='_compute_changes')
    property_id = fields.Many2one('account.asset.asset', string='Property', compute='_compute_changes')
    # booking_id = fields.Many2one('crm.booking', string="Booking")
    spa_id = fields.Many2one('sale.order', 'SPA/Booking')
    partner_id = fields.Many2one('res.partner', string="Customer Name", compute='_compute_changes')
    mobile = fields.Char('Mobile', related='partner_id.mobile', compute='_compute_changes')
    user_id = fields.Many2one('res.users', string="Salesperson", compute='_compute_changes')
    payment_schedule_id = fields.Many2one('payment.schedule',string='Payment Schedule', compute='_compute_changes')

    property_price_ex_vat = fields.Float(string='Property Price Ex VAT', compute='_compute_amounts', store=True)
    vat = fields.Float(string='VAT', compute='_compute_amounts', store=True)
    property_price_inc_vat = fields.Float(string='Property Price Inc. VAT', compute='_compute_amounts', store=True)
    oqood_fee = fields.Float(string='Oqood Fee', compute='_compute_amounts', store=True)
    admin_fee = fields.Float(string='Admin Fee', compute='_compute_amounts', store=True)

    saleamendment_text = fields.Text(string='Sale Amendment Details')
    partner_check = fields.Boolean(string='Change in Customer Name')
    new_partner_id = fields.Many2one('res.partner', string="New Customer Name")
    product_check = fields.Boolean(string='Change in Property')
    new_asset_project_id = fields.Many2one('account.asset.asset', 'New Project', domain="[('project', '=', True)]")
    new_property_id = fields.Many2one('account.asset.asset', string='New Property')
    refund_check = fields.Boolean(string='Cancelation & Refund')

    payment_schedule_check = fields.Boolean('Change in Payment Schedule')
    new_payment_schedule_id = fields.Many2one('payment.schedule',string='New Payment Schedule')
    property_price_check = fields.Boolean('Change in Property Price')
    new_price = fields.Float(string='New Property Price')
    new_vat = fields.Float('Vat')
    new_property_price_inc_vat = fields.Float('Property Price Incl. VAT', compute='_compute_new_price', store=True)
    receipts_ids = fields.One2many('account.payment','amendment_id', string="Receipts", compute='_compute_receipts')

    state = fields.Selection(
        [('draft', 'Draft'), ('under_review', 'Under Sales Manager Review'),
         ('under_verification', 'Accounts Verification'),
         # ('refused', 'Refused'),
         ('approved', 'Approved'),
         ('reject', 'Rejected'), ('cancel', 'Cancelled')], 'Status', default='draft', tracking=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=self.create_date).next_by_code('sale.amendment')
        return super(SaleAmendmentForm, self).create(vals)


    # @api.multi
    @api.depends('sale_id')
    def _compute_data(self):
        for record in self:
            if record.sale_id:
                mrp_order = record.env['mrp.production'].search([('sale_id', '=', record.sale_id.id)])
                if mrp_order:
                    record.processing_id = mrp_order[0].id
                record.signup_date = record.sale_id.date_confirm
                record.partner_id = record.sale_id.partner_id.id
                record.mobile = record.sale_id.partner_id.mobile
                record.email = record.sale_id.partner_id.email
                record.saleperson = record.sale_id.user_id.id
                record.payment_option = record.sale_id.payment_option_id.id
                record.template_id = record.sale_id.template_id.id
            if record.sale_id.order_line:
                record.occupation_programe = record.sale_id.order_line[0].occupation_program
                record.occupation_no = record.sale_id.order_line[0].occupation_no
                record.unit_price = record.sale_id.order_line[0].price_unit
                record.amount_tax = record.sale_id.amount_tax
                record.price_subtotals = record.sale_id.order_line[0].price_subtotal
                record.discount_price = record.sale_id.order_line[0].discount_amount
                if not record.product_id:
                    record.product_id = record.sale_id.order_line[0].product_id.id


    # @api.one
    def draft_back(self):
        self.write({
            'state': 'draft',
        })

    # @api.one
    def submit_forms(self):
        self.write({
            'state': 'under_review',
        })

    # @api.one
    def approved(self):
        self.spa_id.amendment_check = True
        self.spa_id.amendment_id = self.id

        self.write({
            'state': 'approved',
        })
    # @api.one
    def roll_back(self):
        self.spa_id.amendment_check = False
        self.spa_id.amendment_id = False

        self.write({
            'state': 'under_verification',
        })

    # @api.one
    def reject(self):
        self.write({
            'state': 'reject',
        })

    # @api.one
    def review(self):
        self.write({
            'state': 'under_verification',
        })

    # @api.one
    def cancel(self):
        self.write({
            'state': 'cancel',
        })


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    amendment_id = fields.Many2one('sale.amendment', string="Sale Amendment", readonly=True)
