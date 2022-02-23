# See LICENSE file for full copyright and licensing details

from datetime import datetime

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import Warning


class TenancyRentSchedule(models.Model):
    _name = "tenancy.rent.schedule"
    _description = 'Tenancy Rent Schedule'
    _rec_name = "tenancy_id"
    _order = 'start_date'

    
    @api.depends('invc_id.state')
    def compute_move_check(self):
        """
        This method check if invoice state is paid true then move check field.
        @param self: The object pointer
        """
        for data in self:
            data.move_check = bool(data.move_id)
            if data.invc_id and data.invc_id.state == 'posted':
                data.move_check = True

    
    @api.depends('invc_id', 'invc_id.state')
    def compute_paid(self):
        """
        If  the invoice state in paid state then paid field will be true.
        @param self: The object pointer
        """
        for data in self:
            if data.invc_id and data.invc_id.state == 'paid':
                data.paid = True

    note = fields.Text(
        string='Notes',
        help='Additional Notes.')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'tenancy.rent.schedule'))
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency',
        required=True)
    amount = fields.Monetary(
        string='Amount',
        default=0.0,
        currency_field='currency_id',
        help="Rent Amount.")
    start_date = fields.Date(
        string='Date',
        help='Start Date.')
    end_date = fields.Date(
        string='End Date',
        help='End Date.')
    cheque_detail = fields.Char(
        string='Cheque Detail')
    move_check = fields.Boolean(
        #compute='compute_move_check',
        string='Posted',
        store=True)
    rel_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string="Tenant")
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Depreciation Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    paid = fields.Boolean(
        #compute='compute_paid',
        store=True,
        string='Paid',
        help="True if this rent is paid by tenant")
    invc_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')
    inv = fields.Boolean(
        string='Invoiced?')
    pen_amt = fields.Float(
        string='Pending Amount',
        help='Pending Ammount.',
        store=True)
    is_readonly = fields.Boolean(
        string='Readonly')

    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        for rec in self:
            inv_line = {
                'origin': 'tenancy.rent.schedule',
                'name': _('Tenancy(Rent) Cost'),
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id':
                rec.tenancy_id.property_id.income_acc_id.id or False,
                'account_analytic_id': rec.tenancy_id.id or False,
            }
            return [(0, 0, inv_line)]

    
    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        @param self: The object pointer
        """
        inv_obj = self.env['account.move']
        for rec in self:
            # inv_line_values = {
            #     'origin': 'tenancy.rent.schedule',
            #     'name': _('Tenancy(Rent) Cost'),
            #     'price_unit': rec.amount or 0.00,
            #     'quantity': 1,
            #     'account_id':
            #     rec.tenancy_id.property_id.income_acc_id.id or False,
            #     'account_analytic_id': rec.tenancy_id.id or False,
            # }
            # if rec.tenancy_id.multi_prop:
            #     for data in rec.tenancy_id.prop_id:
            #         for account in data.property_ids.income_acc_id:
            #             inv_line_values.update({'account_id': account.id})
            # if self._context.get('penanlty') == 0:
            #     rec.calculate_penalty()
            #     if rec.tenancy_id.penalty < 00:
            #         raise Warning(_(
            #             'The Penalty% must be strictly positive.'))
            #     if rec.tenancy_id.penalty_day < 00:
            #         raise Warning(_('The Penalty Count After Days must be \
            #         strictly positive.'))
            #     amt = rec.amount + rec.penalty_amount
            #     inv_line_values.update({'price_unit': amt or 0.00})
            # if rec.tenancy_id.main_cost >= 0.00:
            #     inv_line_main = {
            #         'origin': 'tenancy.rent.schedule',
            #         'name': 'Maintenance cost',
            #         'price_unit': rec.tenancy_id.main_cost or 0.00,
            #         'quantity': 1,
            #         'account_id': rec.tenancy_id.property_id.income_acc_id.id
            #         or False,
            #         'account_analytic_id': rec.tenancy_id.id or False,
            #     }
            #     if rec.tenancy_id.rent_type_id.renttype == 'Monthly':
            #         m = rec.tenancy_id.main_cost * \
            #             float(rec.tenancy_id.rent_type_id.name)
            #         inv_line_main.update({'price_unit': m})
            #     if rec.tenancy_id.rent_type_id.renttype == 'Yearly':
            #         y = rec.tenancy_id.main_cost * \
            #             float(rec.tenancy_id.rent_type_id.name) * 12
            #         inv_line_main.update({'price_unit': y})
            #     if rec.tenancy_id.multi_prop:
            #         for data in rec.tenancy_id.prop_id:
            #             for account in data.property_ids.income_acc_id:
            #                 inv_line_main.update({'account_id': account.id})
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'move_type': 'out_invoice',
                'property_id': rec.tenancy_id.property_id.id or False,
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'invoice_line_ids': inv_line_values,
            }
            invoice_id = inv_obj.create(inv_values)
            rec.write({'invc_id': invoice_id.id, 'inv': True})
            inv_form_id = self.env.ref('account.view_move_form').id

            return {
                # 'view_type': 'form',
                'view_id': inv_form_id,
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': rec.invc_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    
    def open_invoice(self):
        """
        Description:
            This method is used to open invoce which is created.

        Decorators:
            api.multi
        """
        return {
            # 'view_type': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    
    def post(self):
        """
        Description:
            This method ovride base method for when invoice fully paid
            the paid /posted field will be true. and if we pending half
            payment then remaing amount should be shown as pending amount.
        Decorators:
            api.multi
        """
        res = super(AccountPayment, self).post()
        if self._context.get('asset') or self._context.get('openinvoice'):
            tenancy_obj = self.env['account.analytic.account']
            schedule_obj = self.env['tenancy.rent.schedule']
            for data in tenancy_obj.rent_schedule_ids.browse(
                    self._context.get('active_id')):
                if data:
                    tenan_rent_obj = schedule_obj.search(
                        [('invc_id', '=', data.id)])
                    for data1 in tenan_rent_obj:
                        amt = 0.0
                        if data1.invc_id.state == 'paid':
                            data1.paid = True
                            data1.move_check = True
                        if data1.invc_id:
                            amt = data1.invc_id.residual
                        data1.write({'pen_amt': amt})
        return res
