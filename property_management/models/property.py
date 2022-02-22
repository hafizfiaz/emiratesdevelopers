# See LICENSE file for full copyright and licensing details

from datetime import datetime
import threading

from odoo import _, api, fields, models, sql_db
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, Warning


class PropertyType(models.Model):
    _name = "property.type"
    _description = "Property Type"

    name = fields.Char(
        string='Name',
        required=True)


class RentType(models.Model):
    _name = "rent.type"
    _description = "Rent Type"
    _order = 'sequence_in_view'

    
    @api.depends('name', 'renttype')
    def name_get(self):
        """
        Added name_get for purpose of displaying company name with rent type.
        """
        res = []
        for rec in self:
            rec_str = ''
            if rec.name:
                rec_str += rec.name
            if rec.renttype:
                rec_str += ' ' + rec.renttype
            res.append((rec.id, rec_str))
        return res

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        """
         Added name_search for purpose to search by name and rent type
        """
        args += ['|', ('name', operator, name), ('renttype', operator, name)]
        cuur_ids = self.search(args, limit=limit)
        return cuur_ids.name_get()

    name = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'),
         ('4', '4'), ('5', '5'), ('6', '6'),
         ('7', '7'), ('8', '8'), ('9', '9'),
         ('10', '10'), ('11', '11'), ('12', '12')],
        required=True)
    renttype = fields.Selection(
        [('Monthly', 'Monthly'),
         ('Yearly', 'Yearly'),
         ('Weekly', 'Weekly')],
        string='Rent Type',
        required=True)
    sequence_in_view = fields.Integer(
        string='Sequence')

    @api.constrains('sequence_in_view')
    def _check_value(self):
        for rec in self:
            if rec.search([
                    ('sequence_in_view', '=', rec.sequence_in_view),
                    ('id', '!=', rec.id)]):
                raise ValidationError(_('Sequence should be Unique!'))


class RoomType(models.Model):
    _name = "room.type"
    _description = "Room Type"

    name = fields.Char(
        string='Name',
        required=True)


class Utility(models.Model):
    _name = "utility"
    _description = "Utility"

    name = fields.Char(
        string='Name',
        required=True)


class PlaceType(models.Model):
    _name = 'place.type'
    _description = 'Place Type'

    name = fields.Char(
        string='Place Type',
        required=True)


class PropertyPhase(models.Model):
    _name = "property.phase"
    _description = 'Property Phase'
    _rec_name = 'property_id'

    end_date = fields.Date(
        string='End Date')
    start_date = fields.Date(
        string='Beginning Date')
    commercial_tax = fields.Float(
        string='Commercial Tax (in %)')
    occupancy_rate = fields.Float(
        string='Occupancy Rate (in %)')
    lease_price = fields.Float(
        string='Sales/lease Price Per Month')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    # operational_budget = fields.Float(
    #     string='Operational Budget (in %)')
    company_income = fields.Float(
        string='Company Income Tax CIT (in %)')


class PropertyPhoto(models.Model):
    _name = "property.photo"
    _description = 'Property Photo'
    _rec_name = 'doc_name'

    photos = fields.Binary(
        string='Photos')
    doc_name = fields.Char(
        string='Filename')
    photos_description = fields.Char(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')

class PropertyPhoto(models.Model):
    _name = "property.floor.plans"
    _description = 'Floor Plans'
    _rec_name = 'doc_name'

    photos = fields.Binary(
        string='Photos')
    doc_name = fields.Char(
        string='Filename')
    photos_description = fields.Char(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class PropertyRoom(models.Model):
    _name = "property.room"
    _description = 'Property Room'

    note = fields.Text(
        string='Notes')
    width = fields.Float(
        string='Width')
    height = fields.Float(
        string='Height')
    length = fields.Float(
        string='Length')
    image = fields.Binary(
        string='Picture')
    name = fields.Char(
        string='Name')
    attach = fields.Boolean(
        string='Attach Bathroom')
    type_id = fields.Many2one(
        comodel_name='room.type',
        string='Room Type')
    assets_ids = fields.One2many(
        comodel_name='room.assets',
        inverse_name='room_id',
        string='Assets')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class NearbyProperty(models.Model):
    _name = 'nearby.property'
    _description = 'Nearby Property'

    distance = fields.Float(
        string='Distance (Km)')
    name = fields.Char(
        string='Name')
    type = fields.Many2one(
        comodel_name='place.type',
        string='Type')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


# class PropertyMaintenace(models.Model):
#     _name = "property.maintenance"
#     _inherit = ['mail.thread']
#
#     date = fields.Date(
#         string='Date',
#         default=fields.Date.context_today)
#     cost = fields.Float(
#         string='Cost')
#     type = fields.Many2one(
#         comodel_name='maintenance.type',
#         string='Type')
#     assign_to = fields.Many2one(
#         comodel_name='res.partner',
#         string='Assign To')
#     invc_id = fields.Many2one(
#         comodel_name='account.move',
#         string='Invoice')
#     renters_fault = fields.Boolean(
#         string='Renters Fault',
#         default=False,
#         copy=True)
#     invc_check = fields.Boolean(
#         string='Already Created',
#         default=False)
#     mail_check = fields.Boolean(
#         string='Mail Send',
#         default=False)
#     property_id = fields.Many2one(
#         comodel_name='account.asset.asset',
#         string='Property')
#     account_code = fields.Many2one(
#         comodel_name='account.account',
#         string='Account Code')
#     notes = fields.Text(
#         string='Description',
#         size=100)
#     name = fields.Selection(
#         [('Renew', 'Renew'),
#          ('Repair', 'Repair'),
#          ('Replace', 'Replace')],
#         string='Action',
#         default='Repair')
#     state = fields.Selection(
#         [('draft', 'Draft'),
#          ('progress', 'In Progress'),
#          ('incomplete', 'Incomplete'),
#          ('done', 'Done')],
#         string='State',
#         default='draft')
#     tenant_id = fields.Many2one(
#         comodel_name='tenant.partner',
#         string='Tenant')
#
#     @api.model
#     def _needaction_domain_get(self):
#         return [('state', '=', 'draft')]
#
#     
#     def send_maint_mail(self):
#         """
#         This Method is used to send an email to assigned person.
#         @param self: The object pointer
#         """
#         try:
#             new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
#             uid, context = self.env.uid, self.env.context
#             close_temp = \
#                 'property_management.mail_template_property_maintainance_close'
#             inv_temp = \
#                 'property_management.email_template_edi_invoice_id'
#             maint_temp = \
#                 'property_management.mail_template_property_maintainance'
#             with api.Environment.manage():
#                 self.env = api.Environment(new_cr, uid, context)
#                 try:
#                     current_context = self._context
#                     if current_context.get('cancel'):
#                         template_id = self.env.ref(close_temp)
#                     if current_context.get('invoice'):
#                         template_id = self.env.ref(inv_temp)
#                     else:
#                         template_id = self.env.ref(maint_temp)
#                 except ValueError:
#                     template_id = False
#                 for maint_rec in self:
#                     if not maint_rec.property_id.current_tenant_id.email:
#                         raise Warning(
#                             _("Cannot send email: Assigned user has no \
#                             email address."))
#                     template_id.send_mail(maint_rec.id, force_send=True)
#         finally:
#             self.env.cr.close()
#
#     
#     def reopen_maintenance(self):
#         """
#         This method is used to when maintenance is cancel and we
#         needed to reopen maintenance and change state to draft.
#         @param self: The object pointer
#         """
#         for rec in self:
#             rec.write({'state': 'draft'})
#
#     
#     def start_maint(self):
#         """
#         This Method is used to change maintenance state to progress.
#         @param self: The object pointer
#         """
#         for rec in self:
#             rec.write({'state': 'progress'})
#             thrd_cal = threading.Thread(target=rec.send_maint_mail)
#             thrd_cal.start()
#
#     
#     def cancel_maint(self):
#         """
#         This Method is used to change maintenance state to incomplete.
#         @param self: The object pointer
#         """
#         self.write({'state': 'incomplete'})
#         thrd_cal = threading.Thread(target=self.send_maint_mail)
#         thrd_cal.start()
#
#     @api.onchange('renters_fault')
#     def onchange_renters_fault(self):
#         """
#         If renters_fault is true then it should assign the current
#         tenant to related property in field and if it false remove tenant
#         @param self: The object pointer
#         """
#         analytic_obj = self.env['account.analytic.account']
#         for data in self:
#             if data.property_id:
#                 tncy_ids = analytic_obj.search(
#                     [('property_id', '=', data.property_id.id),
#                      ('state', '!=', 'close')],
#                     limit=1)
#                 for tenancy in tncy_ids:
#                     if data.renters_fault:
#                         data.tenant_id = tenancy.tenant_id.id
#                     else:
#                         data.tenant_id = 0
#
#     @api.onchange('assign_to')
#     def onchanchange_assign(self):
#         """
#         In account code assigne account payable of assign worker.
#         """
#         for data in self:
#             data.account_code = data.assign_to.property_account_payable_id
#
#     
#     def create_invoice(self):
#         """
#         This Method is used to create invoice from maintenance record.
#         @param self: The object pointer
#         """
#         analytic_obj = self.env['account.analytic.account']
#         for data in self:
#             if not data.account_code:
#                 raise Warning(_("Please Select Account Code!"))
#             if not data.property_id.id:
#                 raise Warning(_("Please Select Property!"))
#             tncy_ids = analytic_obj.search(
#                 [('property_id', '=', data.property_id.id),
#                  ('state', '!=', 'close')])
#             if not tncy_ids:
#                 raise Warning(_("No current tenancy for this property!"))
#             else:
#                 for tenancy_data in tncy_ids:
#                     inv_line_values = {
#                         'name': 'Maintenance For ' + data.type.name or "",
#                         'origin': 'property.maintenance',
#                         'quantity': 1,
#                         'account_id':
#                             data.property_id.income_acc_id.id or False,
#                         'price_unit': data.cost or 0.00,
#                     }
#
#                     inv_values = {
#                         'origin': 'Maintenance For ' + data.type.name or "",
#                         'type': 'out_invoice',
#                         'property_id': data.property_id.id,
#                         'partner_id':
#                             tenancy_data.tenant_id.parent_id.id or False,
#                         'account_id': data.account_code.id or False,
#                         'invoice_line_ids': [(0, 0, inv_line_values)],
#                         'amount_total': data.cost or 0.0,
#                         'invoice_date': datetime.now().strftime(
#                             DEFAULT_SERVER_DATE_FORMAT) or False,
#                         'number': tenancy_data.name or '',
#                     }
#                 if data.renters_fault:
#                     inv_values.update(
#                         {'partner_id':
#                             tenancy_data.tenant_id.parent_id.id or False})
#                 else:
#                     inv_values.update({
#                         'partner_id':
#                         tenancy_data.property_id.property_manager.id or False
#                     })
#                 invoice_rec = self.env['account.move'].create(inv_values)
#                 data.write(
#                     {'renters_fault': False,
#                      'invc_check': True,
#                      'invc_id': invoice_rec.id,
#                      'state': 'done'
#                      })
#         thrd_cal = threading.Thread(target=self.send_maint_mail)
#         thrd_cal.start()
#         return True
#
#     
#     def open_invoice(self):
#         """
#         This Method is used to Open invoice from maintenance record.
#         @param self: The object pointer
#         """
#         context = dict(self._context or {})
#         wiz_form_id = self.env.ref('account.view_move_form').id
#         return {
#             'view_type': 'form',
#             'view_id': wiz_form_id,
#             'view_mode': 'form',
#             'res_model': 'account.move',
#             'res_id': self.invc_id.id,
#             'type': 'ir.actions.act_window',
#             'target': 'current',
#             'context': context,
#         }


class CostCost(models.Model):
    _name = "cost.cost"
    _description = 'Cost'
    _order = 'date'

    
    @api.depends('move_id')
    def _compute_move_check(self):
        for rec in self:
            rec.move_check = bool(rec.move_id)

    date = fields.Date(
        string='Date')
    amount = fields.Float(
        string='Amount')
    name = fields.Char(
        string='Description')
    payment_details = fields.Char(
        string='Payment Details')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Purchase Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    remaining_amount = fields.Float(
        string='Remaining Amount',
        help='Shows remaining amount in currency')
    move_check = fields.Boolean(
        compute='_compute_move_check',
        string='Posted',
        store=True)
    rmn_amnt_per = fields.Float(
        string='Remaining Amount In %',
        help='Shows remaining amount in Percentage')
    invc_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')

    
    def create_invoice(self):
        """
        This button Method is used to create account invoice.
        @param self: The object pointer
        """
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        context = dict(self._context or {})
        wiz_form_id = self.env.ref('account.view_move_form').id
        inv_obj = self.env['account.move']
        for rec in self:
            if not rec.property_id.partner_id:
                raise Warning(_('Please Select Partner!'))
            if not rec.property_id.expense_account_id:
                raise Warning(_('Please Select Expense Account!'))

            inv_line_values = {
                'origin': 'Cost.Cost',
                'name':
                    _('Purchase Cost For')+''+rec.property_id.name,
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id': rec.property_id.expense_account_id.id,
            }

            inv_values = {
                'payment_term_id':
                    rec.property_id.payment_term.id or False,
                'partner_id': rec.property_id.partner_id.id or False,
                'move_type': 'in_invoice',
                'property_id': rec.property_id.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'journal_id': account_jrnl_obj and account_jrnl_obj.id or False,
            }
            invoice_rec = inv_obj.create(inv_values)
            rec.write({'invc_id': invoice_rec.id, 'move_check': True})
            return {
                # 'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': rec.invc_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': context,
            }

    
    def open_invoice(self):
        """
        This Method is used to Open invoice
        @param self: The object pointer
        """
        context = dict(self._context or {})
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            # 'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }


class RoomAssets(models.Model):
    _name = "room.assets"
    _description = "Room Assets"

    date = fields.Date(
        string='Date')
    name = fields.Char(
        string='Description')
    type = fields.Selection(
        [('fixed', 'Fixed Assets'),
         ('movable', 'Movable Assets'),
         ('other', 'Other Assets')],
        string='Type')
    qty = fields.Float(
        string='Quantity')
    room_id = fields.Many2one(
        comodel_name='property.room',
        string='Property')


class PropertyInsurance(models.Model):
    _name = "property.insurance"
    _description = "Property Insurance"

    premium = fields.Float(
        string='Premium')
    end_date = fields.Date(
        string='End Date')
    doc_name = fields.Char(
        string='Filename')
    contract = fields.Binary(
        string='Contract')
    start_date = fields.Date(
        string='Start Date')
    name = fields.Char(
        string='Description')
    policy_no = fields.Char(
        string='Policy Number')
    contact = fields.Many2one(
        comodel_name='res.company',
        string='Insurance Comapny')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Related Company')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    payment_mode_type = fields.Selection(
        [('monthly', 'Monthly'),
         ('semi_annually', 'Semi Annually'),
         ('yearly', 'Annually')],
        string='Payment Term')


class PropertyUtility(models.Model):
    _name = "property.utility"
    _description = 'Property Utility'

    note = fields.Text(
        string='Remarks')
    ref = fields.Char(
        string='Reference')
    expiry_date = fields.Date(
        string='Expiry Date')
    issue_date = fields.Date(
        string='Issuance Date')
    utility_id = fields.Many2one(
        comodel_name='utility',
        string='Utility')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact',
        domain="[('tenant', '=', True)]")


class PropertySafetyCertificate(models.Model):
    _name = "property.safety.certificate"
    _description = 'Property Safety Certificate'

    ew = fields.Boolean(
        'EW')
    weeks = fields.Integer(
        'Weeks')
    ref = fields.Char(
        'Reference')
    expiry_date = fields.Date(
        string='Expiry Date')
    name = fields.Char(
        string='Certificate',
        required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact',
        domain="[('tenant', '=', True)]")


class PropertyAttachment(models.Model):
    _name = 'property.attachment'
    _description = 'Property Attachment'

    doc_name = fields.Char(
        string='Filename')
    expiry_date = fields.Date(
        string='Expiry Date')
    contract_attachment = fields.Binary(
        string='Attachment')
    name = fields.Char(
        string='Description',
        required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class SaleCost(models.Model):
    _name = "sale.cost"
    _description = 'Sale Cost'
    _order = 'date'

    
    @api.depends('move_id')
    def _compute_move_check(self):
        for rec in self:
            rec.move_check = bool(rec.move_id)

    date = fields.Date(
        string='Date')
    amount = fields.Float(
        string='Amount')
    name = fields.Char(
        string='Description')
    payment_details = fields.Char(
        string='Payment Details')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Purchase Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    remaining_amount = fields.Float(
        string='Remaining Amount',
        help='Shows remaining amount in currency')
    move_check = fields.Boolean(
        string='Posted',
        compute='_compute_move_check',
        store=True)
    rmn_amnt_per = fields.Float(
        string='Remaining Amount In %',
        help='Shows remaining amount in Percentage')
    invc_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')

    
    def create_invoice(self):
        """
        This button Method is used to create account invoice.
        @param self: The object pointer
        """
        if not self.property_id.customer_id:
            raise Warning(_('Please Select Customer!'))
        if not self.property_id.income_acc_id:
            raise Warning(_('Please Configure Income Account from Property!'))
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)

        inv_line_values = {
            'origin': 'sale.cost',
            'name': _('Purchase Cost For')+''+self.property_id.name,
            'price_unit': self.amount or 0.00,
            'quantity': 1,
            'account_id': self.property_id.income_acc_id.id,
        }

        inv_values = {
            'payment_term_id': self.property_id.payment_term.id or False,
            'partner_id': self.property_id.customer_id.id or False,
            'move_type': 'out_invoice',
            'property_id': self.property_id.id or False,
            'invoice_line_ids': [(0, 0, inv_line_values)],
            'journal_id': account_jrnl_obj and account_jrnl_obj.id or False,
        }
        acc_id = self.env['account.move'].create(inv_values)
        self.write({'invc_id': acc_id.id, 'move_check': True})
        context = dict(self._context or {})
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            # 'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }

    
    def open_invoice(self):
        """
        This Method is used to Open invoice
        @param self: The object pointer
        """
        context = dict(self._context or {})
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            # 'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }
