from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


# class StatusLog(models.Model):
#     _inherit = "status.log"
#
#     termination_id = fields.Many2one('termination.process', string='Termination Process')


class TerminationProcess(models.Model):
    _name = 'termination.process'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Termination Process'

    def _get_default_model_ids(self):
        return self.env['ir.model'].search([('model', '=', self._name)])[0].id

    subject = fields.Char('Subject')
    sequence = fields.Char('Sequence', readonly=True)
    clearance_type = fields.Many2one('clearance.type', 'Approval Type')
    # booking_id = fields.Many2one('crm.booking', 'Booking', related='spa.booking_id')
    spa = fields.Many2one('sale.order', 'Related SPA/Booking')
    project = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property = fields.Many2one('account.asset.asset', 'Property')
    model_id = fields.Many2one('ir.model', string='Projects', default=_get_default_model_ids)

    spa_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_legal_review_print', 'Under legal Review for Print'),
        ('under_acc_verification_print', 'Under Account Verification for Print'),
        ('under_confirmation_print', 'Under Confirmation for Print'),
        ('unconfirmed_print', 'Unconfirmed SPA OK for Print'),
        ('under_legal_review', 'Under Legal Review'),
        ('under_acc_verification', 'Under Accounts Verify'),
        ('under_approval', 'Under Approval'),
        ('sale', 'Approved SPA'),
        ('refund_cancellation', 'Refund Cancellation'),
        ('reject', 'Rejected'),
        ('paid', 'Approved SPA-Paid'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='SPA Status', related='spa.state', readonly=True)

    # booking_status = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('under_discount_approval', 'Under Discount Approval'),
    #     ('tentative_booking', 'Tentative Booking'),
    #     ('review', 'Under Review'),
    #     ('confirm_spa', 'Confirmed for SPA'),
    #     ('approved', 'Approved'),
    #     ('rejected', 'Rejected'),
    #     ('cancel', 'Cancel')
    # ], string='Booking Status', related='booking_id.is_buy_state', readonly=True)
    total_spa = fields.Float('Total SPA Value', compute='_spavalue', store=True)
    total_collection = fields.Float('Total Collection', compute='totalcoll', store=True)
    total_collection_perc = fields.Float(string="Total Collection(%)", compute='totalCollection', store=True)
    realized_collection = fields.Float('Total Amount (Realized Collections)', compute='_spapdc', store=True)
    realized_collection_perc = fields.Float(string="Total Amount(%)", compute='realizedCollection', store=True)
    pending_collections = fields.Float('Pending Collections', compute='pending', store=True)
    pending_collections_perc = fields.Float(string="Pending Collections(%)", compute='pendingCollection', store=True)
    total_due_amount = fields.Float('Total Due Amount', compute='installment', store=True)
    total_due_amount_perc = fields.Float(string="Total Due Amount(%)", compute='dueamountperc', store=True)
    due_balance_collections = fields.Float('Balance Due Collection', compute='dueamount', store=True)
    due_balance_perc = fields.Float(string="Balance Due Collection(%)", compute='duebalanceperc', store=True)
    # unit_type_id = fields.Many2one('unit.type', 'Type', related='property.unit_type_id')
    size = fields.Float('Size(Sqft)')
    parking = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Parking', related='property.parking', store=True)
    oqood_status = fields.Many2one('oqood.status', 'Oqood Status', related='spa.oqood_status', store=True)
    admin_status = fields.Many2one('admin.status', 'Admin Status', related='spa.admin_status', store=True)
    receivable_status = fields.Many2one('receivable.status', 'Receivable Status', related='spa.receivable_status_id',
                                        store=True)
    # tag_ids = fields.Many2many('crm.lead.tag', 'crm_lead_tag_rel', 'lead_id', 'tag_id', string='Tags',
    #                            related='spa.tag_ids')
    discount_amount = fields.Float('Discount Amount')
    discount_amount_perc = fields.Float('Discount Percentage', compute="discountperc", store=True)
    notes = fields.Text('Sale Admin Team Remarks')
    # handover_lines = fields.One2many('handover.clearance.lines', 'termination_id')

    @api.onchange('property')
    def get_spa(self):
        sale_orders = self.env['sale.order'].search(
            [('property_id', '=', self.property.id), ('asset_project_id', '=', self.project.id),
             ('state', 'not in', ['draft', 'cancel', 'rejected'])])
        if sale_orders:
            self.spa = sale_orders[0].id
        else:
            self.spa = False
    #
    # @api.model
    # def default_get(self, fields):
    #     res = super(TerminationProcess, self).default_get(fields)
    #     handover_lines = []
    #     description =['Title Deed Fee','Hanover Fee','Dewa Activation Fee','Service Charges']
    #     for rec in description:
    #         line =(0, 0, {
    #             'detail': rec
    #         })
    #         handover_lines.append(line)
    #         res.update({
    #             'handover_lines': handover_lines
    #         })
    #     return res

    @api.depends('discount_amount', 'property.total_price')
    def discountperc(self):
        for rec in self:
            if rec.discount_amount and rec.property.total_price:
                rec.discount_amount_perc = rec.discount_amount / rec.property.total_price * 100

    @api.depends('total_collection', 'spa.total_spa_value')
    def totalCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.total_collection_perc = rec.total_collection / rec.spa.total_spa_value * 100

    @api.depends('realized_collection', 'spa.total_spa_value')
    def realizedCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.realized_collection_perc = rec.realized_collection / rec.spa.total_spa_value * 100

    @api.depends('pending_collections', 'spa.total_spa_value')
    def pendingCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.pending_collections_perc = rec.pending_collections / rec.spa.total_spa_value * 100

    @api.depends('total_due_amount', 'spa.total_spa_value')
    def dueamountperc(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.total_due_amount_perc = rec.total_due_amount / rec.spa.total_spa_value * 100

    @api.depends('due_balance_collections', 'spa.total_spa_value')
    def duebalanceperc(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.due_balance_collections:
                rec.due_balance_perc = rec.due_balance_collections / rec.spa.total_spa_value * 100

    @api.depends('spa', 'spa.total_spa_value')
    def _spavalue(self):
        for rec in self:
            rec.total_spa = rec.spa.total_spa_value

    @api.depends('spa', 'spa.matured_pdcs')
    def _spapdc(self):
        for rec in self:
            rec.realized_collection = rec.spa.matured_pdcs

    @api.depends('spa', 'spa.total_receipts')
    def totalcoll(self):
        for rec in self:
            rec.total_collection = rec.spa.total_receipts

    @api.depends('spa', 'spa.pending_balance')
    def pending(self):
        for rec in self:
            rec.pending_collections = rec.spa.pending_balance

    @api.depends('spa', 'spa.instalmnt_bls_pend_plus_admin_oqood')
    def installment(self):
        for rec in self:
            rec.total_due_amount = rec.spa.instalmnt_bls_pend_plus_admin_oqood

    @api.depends('spa', 'spa.balance_due_collection')
    def dueamount(self):
        for rec in self:
            rec.due_balance_collections = rec.spa.balance_due_collection

    def action_view_spa_invoices(self):

        return {
            'name': _("Invoices"),
            'view_mode': 'tree,form',
            # 'context': ctx,
            'domain': [('id', 'in', self.spa.all_invoice_ids.ids)],
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'context': {
                'tree_view_ref': 'account.view_out_invoice_tree',
                'create': False,
                'edit': False,
                'duplicate': False
            }
        }

    name = fields.Char('Name', related='spa.partner_id.name', store=True)
    partner_id = fields.Many2one('res.partner', string='Name', related='spa.partner_id', store=True)
    mobile = fields.Char('Mobile', related='spa.partner_id.mobile', store=True)
    email = fields.Char("Email", related='spa.partner_id.email', store=True)
    # nationality = fields.Char("Nationality", related='spa.partner_id.nationality')
    address = fields.Char("Address", related='spa.partner_id.street', store=True)
    total_spa_customer = fields.Integer('Total SPA', compute="get_totals", store=True)
    # total_bookings = fields.Integer("Total Bookings", compute="get_totals")
    due_amount_to_clear = fields.Char("Due Amount to Clear")
    account_remarks = fields.Text("Accounts Remarks")
    stage_id = fields.Many2one('project.stage', 'Status')
    escrow = fields.Float(string="Escrow Receipts", compute='_escrow', store=True)
    escrow_perc = fields.Float(string="Escrow Receipt Percentage", compute='escrow_perct', store=True)
    non_escrow = fields.Float(string="Non Escrow Receipts", compute='_escrow', store=True)
    non_escrow_perc = fields.Float(string="Non Escrow Receipt Percentage", compute="non_escrow_perct", store=True)
    total_escrow = fields.Float("Total", compute="escrow_tot", store=True)
    total_escrow_perc = fields.Float("Total Percentage", compute="tot_escrow_perct", store=True)

    # status_log_ids = fields.One2many('status.log', 'termination_id', string='Status Logs')
    state_change = fields.Char(compute="get_state", store=True, string="State Change")

    @api.depends('stage_id')
    def get_state(self):
        for rec in self:
            rec.state_change = rec.stage_id.name

    #         old_state = False
    #         days = False
    #         # days = False
    #         prevous_log = rec.env['status.log'].search([('model_name', '=', rec._name), ('record_id', '=', rec.id)],
    #                                                    order='updated_date DESC', limit=1)
    #         if prevous_log:
    #             old_state = prevous_log.status_to
    #             current_date = datetime.now()
    #             prevous_log_date = prevous_log.updated_date
    #             dates_diff = current_date.date() - prevous_log_date.date()
    #             days = dates_diff.days
    #         rec.env['status.log'].create({
    #             'model_name': rec._name,
    #             'record_id': rec.id,
    #             'termination_id': rec.id,
    #             'status_from': old_state,
    #             'status_to': rec.stage_id.name,
    #             'days': days
    #         })

    @api.depends('spa.receipt_ids')
    def _escrow(self):
        for rec in self:
            for tot in rec.spa.receipt_ids:
                if tot.sub_type.name == 'Escrow' and tot.state == 'posted':
                    rec.escrow += tot.amount
                if tot.sub_type.name != 'Escrow' and tot.state == 'posted':
                    rec.non_escrow += tot.amount

    @api.depends('escrow', 'spa.total_spa_value')
    def escrow_perct(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.escrow:
                rec.escrow_perc = rec.escrow / rec.spa.total_spa_value * 100

    @api.depends('non_escrow', 'spa.total_spa_value')
    def non_escrow_perct(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.non_escrow:
                rec.non_escrow_perc = rec.non_escrow / rec.spa.total_spa_value * 100

    @api.depends('escrow', 'non_escrow')
    def escrow_tot(self):
        for rec in self:
            rec.total_escrow = rec.escrow + rec.non_escrow

    @api.depends('total_escrow', 'spa.total_spa_value')
    def tot_escrow_perct(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.total_escrow:
                rec.total_escrow_perc = rec.total_escrow / rec.spa.total_spa_value * 100

    @api.model
    def create(self, vals):
        if not vals.get('sequence', ''):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'termination.process')
        result = super(TerminationProcess, self).create(vals)
        stage_id = vals.get('stage_id', False)
        if stage_id:
            stage_ids = self.env['project.stage'].search([('id', '=', stage_id)])
            if stage_ids.mail_template_id:
                model_id = self.env['ir.model'].search([('model', '=', self._name)])
                email_template = stage_ids.mail_template_id
                email_template.email_to = stage_ids.get_partner_ids(stage_ids.responsible_id)
                email_template.model_id = model_id.id
                email_template.send_mail(result.id, force_send=True)
            # for line in stage_ids.related_task_ids:
            #     self.env['related.task.action'].create({
            #         'name': line.name,
            #         'responsible_id': line.responsible_id.id,
            #         'remarks': line.remarks,
            #         'termination_id': result.id,
            #     })
        return result

    @api.depends('partner_id')
    def get_totals(self):
        for rec in self:
            spa_ids = rec.env['sale.order'].search([('partner_id', '=', rec.partner_id.id), ('state', '!=', 'cancel')])
            if spa_ids and self.partner_id:
                rec.total_spa_customer = len(spa_ids.ids)
            else:
                rec.total_spa_customer = False

    @api.model
    def old_termination_fields(self):
        sos = self.env['termination.process'].search([])
        for rec in sos:
            if rec.spa:
                rec.partner_id = rec.spa.partner_id.id
                rec.mobile = rec.spa.partner_id.mobile
                rec.email = rec.spa.partner_id.email
                rec.address = rec.spa.partner_id.street
                rec.oqood_status = rec.spa.oqood_status
                rec.admin_status = rec.spa.admin_status
                rec.receivable_status = rec.spa.receivable_status_id
                rec.property = rec.spa.property_id
                rec.project = rec.spa.asset_project_id

    def write(self, vals):
        result = super(TerminationProcess, self).write(vals)
        stage_id = vals.get('stage_id', False)
        if stage_id:
            stage_ids = self.env['project.stage'].search([('id', '=', stage_id)])
            if stage_ids.mail_template_id:
                model_id = self.env['ir.model'].search([('model', '=', self._name)])
                email_template = stage_ids.mail_template_id
                email_template.email_to = stage_ids.get_partner_ids(stage_ids.responsible_id)
                email_template.model_id = model_id.id
                email_template.send_mail(self.id, force_send=True)
            if self.env.user.id not in stage_ids.responsible_id.ids:
                raise UserError(_("Only Responsible Person Can Change the Stage"))
            # new_list = []
            # old_tasks_ids = self.related_task_ids.ids
            # if stage_ids:
            #     for line in stage_ids.related_task_ids:
            #         new_id = self.env['related.task.action'].create({
            #             'name': line.name,
            #             'responsible_id': line.responsible_id.id,
            #             'remarks': line.remarks,
            #             'termination_id': self.id,
            #         })
            #         new_list.append(new_id.id)
            # tasks = new_list + old_tasks_ids
            # vals['related_task_ids'] = [(6, 0, tasks)]
        return result



# class HandoverLines(models.Model):
#     _inherit = 'handover.clearance.lines'
#     _description = 'Handover Lines'
#
#     termination_id = fields.Many2one("termination.process")


# class ProjectTask(models.Model):
#     _inherit = 'project.task.type'
#
#     clearance_type = fields.Many2many('clearance.type', string='Approval IDs')
