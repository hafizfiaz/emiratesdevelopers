# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    rental_journal_id = fields.Many2one('account.journal', string='Rental Journal')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    rental_id = fields.Many2one('account.analytic.account', string='Rental Tenancy')


# class AccountVoucherCollection(models.Model):
#     _inherit = 'account.voucher.collection'
#
#     rental_id = fields.Many2one('account.analytic.account', string='Rental Tenancy')


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    rental = fields.Boolean(string='Rental')
    rental_schedule_id = fields.Many2one('tenancy.rent.schedule', string='Rental Schedule')


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    name = fields.Char(string='Subject', index=True, required=True, tracking=True)
    # tenant_partner_id = fields.Many2one('res.partner', string='Tenant', domain = [('is_tenant', '=', True)])
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    # pdc_receipt_ids = fields.One2many('account.voucher.collection', 'rental_id', 'PDC Receipts')
    receipt_ids = fields.One2many('account.payment', 'rental_id', 'Receipts')
    accounting_ledger_id = fields.Many2one('account.account','Accounting Ledger', tracking=True)

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        # self.accounting_ledger_id = self.asset_project_id.rental_journal_id.default_debit_account_id.id
        self.accounting_ledger_id = 1
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    
    def create_rent_schedule(self):
        """
        This button method is used to create rent schedule Lines.
        @param self: The object pointer
        """
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise Warning(
                        _('End date must be greater than start date.'))
                wek_diff = (d2 - d1)
                wek_tot1 = (wek_diff.days) / (interval * 7)
                wek_tot = (wek_diff.days) % (interval * 7)
                if wek_diff.days == 0:
                    wek_tot = 1
                if wek_tot1 > 0:
                    for wek_rec in range(int(wek_tot1)):
                        rent_obj.create(
                            {'start_date': d1,
                             'amount': tenancy_rec.rent * interval or 0.0,
                             'asset_project_id': tenancy_rec.asset_project_id
                                                 and tenancy_rec.asset_project_id.id or False,
                             'property_id': tenancy_rec.property_id
                                            and tenancy_rec.property_id.id or False,
                             'tenancy_id': tenancy_rec.id,
                             'currency_id': tenancy_rec.currency_id.id
                                            or False,
                             'rel_tenant_id': tenancy_rec.tenant_id.id
                             })
                        d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    one_day_rent = 0.0
                    if tenancy_rec.rent:
                        one_day_rent = (tenancy_rec.rent) / (7 * interval)
                    rent_obj.create(
                        {'start_date': d1.strftime(
                            DEFAULT_SERVER_DATE_FORMAT),
                            'amount': (one_day_rent * (wek_tot)) or 0.0,
                            'asset_project_id': tenancy_rec.asset_project_id
                                                and tenancy_rec.asset_project_id.id or False,
                            'property_id': tenancy_rec.property_id
                                           and tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id
                        })
            elif tenancy_rec.rent_type_id.renttype != 'Weekly':
                if tenancy_rec.rent_type_id.renttype == 'Monthly':
                    interval = int(tenancy_rec.rent_type_id.name)
                if tenancy_rec.rent_type_id.renttype == 'Yearly':
                    interval = int(tenancy_rec.rent_type_id.name) * 12
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                diff = abs((d1.year - d2.year) * 12 + (d1.month - d2.month))
                tot_rec = diff / interval
                tot_rec2 = diff % interval
                if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                    tot_rec2 += 1
                if diff == 0:
                    tot_rec2 = 1
                if tot_rec > 0:
                    for rec in range(int(tot_rec)):
                        rent_obj.create(
                            {'start_date': d1,
                             'amount': tenancy_rec.rent * interval or 0.0,
                             'asset_project_id': tenancy_rec.asset_project_id
                                                 and tenancy_rec.asset_project_id.id or False,
                             'property_id': tenancy_rec.property_id
                                            and tenancy_rec.property_id.id or False,
                             'tenancy_id': tenancy_rec.id,
                             'currency_id': tenancy_rec.currency_id.id
                                            or False,
                             'rel_tenant_id': tenancy_rec.tenant_id.id
                             })
                        d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1,
                        'amount': tenancy_rec.rent * tot_rec2 or 0.0,
                        'asset_project_id': tenancy_rec.asset_project_id
                                            and tenancy_rec.asset_project_id.id or False,
                        'property_id': tenancy_rec.property_id
                                       and tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
                    })
            return tenancy_rec.write({'rent_entry_chck': True})

    
    def create_rent_schedule_landlord(self):
        """
        This button method is used to create rent schedule Lines.
        @param self: The object pointer
        """
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            amount = tenancy_rec.landlord_rent
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise Warning(
                        _('End date must be greater than start date.'))
                wek_diff = (d2 - d1)
                wek_tot1 = (wek_diff.days) / (interval * 7)
                wek_tot = (wek_diff.days) % (interval * 7)
                if wek_diff.days == 0:
                    wek_tot = 1
                if wek_tot1 > 0:
                    for wek_rec in range(wek_tot1):
                        rent_obj.create(
                            {
                                'start_date': d1,
                                'amount': amount * interval or 0.0,
                                'asset_project_id': tenancy_rec.asset_project_id
                                                    and tenancy_rec.asset_project_id.id or False,
                                'property_id': tenancy_rec.property_id and
                                               tenancy_rec.property_id.id or False,
                                'tenancy_id': tenancy_rec.id,
                                'currency_id': tenancy_rec.currency_id.id or
                                               False,
                                'rel_tenant_id': tenancy_rec.tenant_id.id
                            })
                        d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    one_day_rent = 0.0
                    if amount:
                        one_day_rent = (amount) / (7 * interval)
                    rent_obj.create({
                        'start_date': d1.strftime(
                            DEFAULT_SERVER_DATE_FORMAT),
                        'amount': (one_day_rent * (wek_tot)) or 0.0,
                        'asset_project_id': tenancy_rec.asset_project_id
                                            and tenancy_rec.asset_project_id.id or False,
                        'property_id': tenancy_rec.property_id and
                                       tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
                    })
            elif tenancy_rec.rent_type_id.renttype != 'Weekly':
                if tenancy_rec.rent_type_id.renttype == 'Monthly':
                    interval = int(tenancy_rec.rent_type_id.name)
                if tenancy_rec.rent_type_id.renttype == 'Yearly':
                    interval = int(tenancy_rec.rent_type_id.name) * 12
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                diff = abs((d1.year - d2.year) * 12 + (d1.month - d2.month))
                tot_rec = diff / interval
                tot_rec2 = diff % interval
                if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                    tot_rec2 += 1
                if diff == 0:
                    tot_rec2 = 1
                if tot_rec > 0:
                    tot_rec = int(tot_rec)
                    for rec in range(tot_rec):
                        rent_obj.create({
                            'start_date': d1.strftime(
                                DEFAULT_SERVER_DATE_FORMAT),
                            'amount': amount * interval or 0.0,
                            'asset_project_id': tenancy_rec.asset_project_id
                                                and tenancy_rec.asset_project_id.id or False,
                            'property_id': tenancy_rec.property_id and
                                           tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or
                                           False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id
                        })
                        d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'amount': amount * tot_rec2 or 0.0,
                        'asset_project_id': tenancy_rec.asset_project_id
                                            and tenancy_rec.asset_project_id.id or False,
                        'property_id': tenancy_rec.property_id and
                                       tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id
                    })
        return self.write({'rent_entry_chck': True})

    
    def button_receive(self):
        """
        This button method is used to open the related
        account payment form view.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        acc_pay_form = self.env.ref(
            'account.view_account_payment_form')
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        payment_obj = self.env['account.payment']
        payment_method_id = self.env.ref(
            'account.account_payment_method_manual_in')
        for tenancy_rec in self:
            if tenancy_rec.acc_pay_dep_rec_id and \
                    tenancy_rec.acc_pay_dep_rec_id.id:
                return {
                    # 'view_type': 'form',
                    'view_id': acc_pay_form.id,
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'res_id': tenancy_rec.acc_pay_dep_rec_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': self._context,
                }
            if tenancy_rec.deposit == 0.00:
                raise Warning(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise Warning(
                    _('The deposit amount must be strictly positive.'))
            if not tenancy_rec.asset_project_id.rental_journal_id:
                raise Warning(
                    _('Please Select Rental Journal in project.'))
            vals = {
                'partner_id': tenancy_rec.tenant_id.parent_id.id,
                'partner_type': 'customer',
                'journal_id': tenancy_rec.asset_project_id.rental_journal_id.id,
                'payment_type': 'inbound',
                'communication': 'Deposit Received',
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
                'asset_project_id': tenancy_rec.asset_project_id.id,
                'payment_method_id': payment_method_id.id
            }
            payment_id = payment_obj.create(vals)
            return {
                'view_mode': 'form',
                'view_id': acc_pay_form.id,
                # 'view_type': 'form',
                'res_id': payment_id.id,
                'res_model': 'account.payment',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': {
                    'close_after_process': True,
                }
            }


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"

    
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

    paid = fields.Boolean(
        compute='compute_paid',
        store=True,
        string='Paid',
        help="True if this rent is paid by tenant")
    move_check = fields.Boolean(
        compute='compute_move_check',
        string='Posted',
        store=True)
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    state = fields.Selection([('new', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Cancelled')],
                             default='new', compute='compute_state', store=True)

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    
    @api.depends('tenancy_id', 'tenancy_id.state')
    def compute_state(self):
        for data in self:
            if data.tenancy_id and data.tenancy_id.state in ['template', 'draft', 'pending']:
                data.state = 'new'
            if data.tenancy_id and data.tenancy_id.state in ['open', 'close']:
                data.state = 'confirm'
            if data.tenancy_id and data.tenancy_id.state in ['cancelled']:
                data.state = 'cancel'

    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        @param self: The object pointer
        """
        inv_obj = self.env['account.move']
        for rec in self:
            if not rec.tenancy_id.asset_project_id.rental_journal_id:
                raise Warning(
                    _('Please Select Rental Journal in project.'))
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'rental_schedule_id': rec.id or False,
                'move_type': 'out_invoice',
                'rental': True,
                'asset_project_id': rec.tenancy_id.asset_project_id.id or False,
                'property_id': rec.tenancy_id.property_id.id or False,
                'invoice_date': rec.start_date,
                # 'date_due':  rec.start_date,
                'invoice_line_ids': inv_line_values,
            }
            invoice_id = inv_obj.create(inv_values)
            # invoice_id.action_post()
            rec.write({'invc_id': invoice_id.id, 'inv': True})
            # inv_form_id = self.env.ref('account.invoice_form').id

            return {
                # 'view_id': inv_form_id,
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': rec.invc_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def create_rental_invoice_auto(self):
        inv_obj = self.env['account.move']
        tenancy_rent = self.env['tenancy.rent.schedule'].search(
            [('start_date', '<=', datetime.now().date()), ('inv', '!=', True), ('tenancy_id.state', '!=', 'cancelled'),
             ('tenancy_id.property_id', '!=', False), ('tenancy_id.asset_project_id', '!=', False),
             ('state', '=', 'confirm')])
        for rec in tenancy_rent:
            if not rec.tenancy_id.asset_project_id.rental_journal_id:
                raise Warning(
                    _('Please Select Rental Journal in project.'))
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'partner_id': rec.tenancy_id.tenant_id.parent_id.id or False,
                'rental_schedule_id': rec.id or False,
                'move_type': 'out_invoice',
                'rental': True,
                'asset_project_id': rec.tenancy_id.asset_project_id.id or False,
                'property_id': rec.tenancy_id.property_id.id or False,
                'invoice_date': rec.start_date,
                # 'date_due':  rec.start_date,
                'invoice_line_ids': inv_line_values,
            }
            invoice_id = inv_obj.create(inv_values)
            # invoice_id.action_post()
            rec.write({'invc_id': invoice_id.id, 'inv': True})
    
    def create_rental_invoice_auto_reverse(self):
        tenancy_rent = self.env['tenancy.rent.schedule'].search(
            [('start_date', '<=', datetime.now().date()), ('inv', '!=', True), ('tenancy_id.state', '!=', 'cancelled'),
             ('tenancy_id.property_id', '!=', False),('tenancy_id.asset_project_id', '!=', False),('state', '=', 'confirm')])
        for rec in tenancy_rent:
            rec.write({'invc_id': False, 'inv': False})

    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        for rec in self:
            inv_line = {
                # 'origin': 'tenancy.rent.schedule',
                'name': _('Rental Invoice'),
                'asset_project_id': rec.tenancy_id.asset_project_id.id or False,
                'property_id': rec.tenancy_id.property_id.id or False,
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id':
                    rec.tenancy_id.accounting_ledger_id.id or False,
                # 'account_analytic_id': rec.tenancy_id.id or False,
            }
            return [(0, 0, inv_line)]
