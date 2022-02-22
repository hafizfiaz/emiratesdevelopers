# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
from collections import defaultdict
from urllib import parse
import time




class SMSClient(models.Model):

    _inherit = 'sms.smsclient'


    def _check_permissions(self):
        if self.env.context:
            if self.env.context['active_model'] in ['account.payment', 'bounced.email.wiz']:
                return True
        self._cr.execute('select * from res_smsserver_group_rel where  uid=%s' % ( self.env.uid))
        data = self._cr.fetchall()
        if len(data) <= 0:
            return False
        return True

class CollectionsTeam(models.Model):
    _name = 'collections.team'
    _description = 'Collection Team'

    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)

class SequenceMixin(models.AbstractModel):
    _inherit = 'sequence.mixin'

    def _set_next_sequence(self):
        self.ensure_one()
        last_sequence = self._get_last_sequence()
        if self._name == 'account.move':
            if last_sequence:
                name_split = last_sequence.split('/')
                if name_split[0] == 'False':
                    last_sequence = last_sequence.replace(name_split[0], self.journal_id.code)
        new = not last_sequence
        if new:
            last_sequence = self._get_last_sequence(relaxed=True) or self._get_starting_sequence()

        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            format_values['seq'] = 0
            format_values['year'] = self[self._sequence_date_field].year % (10 ** format_values['year_length'])
            format_values['month'] = self[self._sequence_date_field].month
        format_values['seq'] = format_values['seq'] + 1
        name_2 = format.format(**format_values)
        if self._name == 'account.move':
            while len(self.search([('name','=', name_2)])) > 0:
                second_split = name_2.split('/')
                new_num = str(int(second_split[-1]) + 1).zfill(len(second_split[-1]))
                name_2 = name_2.replace(second_split[-1], str(new_num))
        self[self._sequence_field] = name_2
        self._compute_split_sequence()

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def change_false_jv_name(self, record, prefix):
        for rec in self.search([('id','=',record)]):
            name_2 = rec.name
            second_split = name_2.split('/')
            name_2 = name_2.replace(second_split[0], prefix)
            rec.name = name_2

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = [m.invoice_filter_type_domain] if m.invoice_filter_type_domain else ['general','pdc']
            company_id = m.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id), ('type', 'in', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.constrains('name', 'journal_id', 'state')
    def _check_unique_sequence_number(self):
        # return True
        moves = self.filtered(lambda move: move.state == 'posted')
        if not moves:
            return

        self.flush(['name', 'journal_id', 'move_type', 'state'])

        # /!\ Computed stored fields are not yet inside the database.
        self._cr.execute('''
            SELECT move2.id, move2.name
            FROM account_move move
            INNER JOIN account_move move2 ON
                move2.name = move.name
                AND move2.journal_id = move.journal_id
                AND move2.move_type = move.move_type
                AND move2.id != move.id
            WHERE move.id IN %s AND move2.state = 'posted'
        ''', [tuple(moves.ids)])
        res = self._cr.fetchall()
        if res:
            raise ValidationError(_('Posted journal entry must have an unique sequence number per company.\n'
                                    'Problematic numbers: %s\n') % ', '.join(r[1] for r in res))

    @api.model
    def _search_default_journal(self, journal_types):
        if self._context.get('default_payment_type'):
            return
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]

        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            company = self.env['res.company'].browse(company_id)

            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)

        return journal

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        # if not self._context.get('bounce_payment'):
        if res.name and res.name != '/':
            old_name = res.name
            name_split = old_name.split('/')
            if name_split[0] == 'False':
                old_name = old_name.replace(name_split[0], res.journal_id.code)
            if name_split[0] != res.journal_id.code:
                # res.name = old_name.replace(name_split[0], res.journal_id.code)
                # r = self.sorted(lambda m: (m.date, m.ref or '', m.id))
                highest_name = res._get_last_sequence()
                second_split = highest_name.split('/')
                if name_split[-1] <= second_split[-1]:
                    new_num = str(int(second_split[-1]) + 1).zfill(len(second_split[-1]))
                    second_name = old_name.replace(name_split[0], res.journal_id.code)
                    res.name = second_name.replace(name_split[-1], str(new_num))
            else:
                seq_key = 1
                if len(self.search([('name', '=', res.name)])) > 1:
                    name_2 = old_name
                    while seq_key==1:
                        second_split = name_2.split('/')
                        new_num = str(int(second_split[-1]) + 1).zfill(len(second_split[-1]))
                        name_2 = name_2.replace(name_split[-1], str(new_num))
                        if len(self.search([('name', '=', name_2)])) < 1:
                            res.name = name_2
                            seq_key=0
            if len(self.search([('name','=', res.name)])) > 1:
                seq_key = 1
                if len(self.search([('name', '=', res.name)])) > 1:
                    name_2 = old_name
                    while seq_key==1:
                        second_split = name_2.split('/')
                        new_num = str(int(second_split[-1]) + 1).zfill(len(second_split[-1]))
                        name_2 = name_2.replace(second_split[-1], str(new_num))
                        if len(self.search([('name', '=', name_2)])) < 1:
                            res.name = name_2
                            seq_key=0
            if len(self.search([('name', '=', res.name)])) > 1:
                raise UserError('Entry with same name already exist!')
        return res


    @api.model
    def _get_default_journal(self):
        ''' Get the default journal.
        It could either be passed through the context using the 'default_journal_id' key containing its id,
        either be determined by the default type.
        '''
        move_type = self._context.get('default_move_type', 'entry')
        if move_type in self.get_sale_types(include_receipts=True):
            journal_types = ['sale']
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_types = ['purchase']
        else:
            journal_types = self._context.get('default_move_journal_types', ['pdc', 'general'])

        if self._context.get('default_journal_id'):
            journal = self.env['account.journal'].browse(self._context['default_journal_id'])

            if move_type != 'entry' and journal.type not in journal_types:
                raise UserError(_(
                    "Cannot create an invoice of type %(move_type)s with a journal having %(journal_type)s as type.",
                    move_type=move_type,
                    journal_type=journal.type,
                ))
        else:
            journal = self._search_default_journal(journal_types)

        return journal

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        # if not self.journal_id:
        #     return '/'
        def journal_key(move):
            if not move.journal_id.refund_sequence and move.payment_id:
                return (move.journal_id, move.journal_id.code and move.move_type)
            return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

        def date_key(move):
            return (move.date.year, move.date.month)

        grouped = defaultdict(  # key: journal_id, move_type
            lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                lambda: {
                    'records': self.env['account.move'],
                    'format': False,
                    'format_values': False,
                    'reset': False
                }
            )
        )
        self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
        highest_name = self[0]._get_last_sequence() if self else False
        if highest_name:
            name_split = highest_name.split('/')
            if name_split[0] == 'False':
                highest_name = highest_name.replace(name_split[0], self.journal_id.code)

        # Group the moves by journal and month
        for move in self:
            if not highest_name and move == self[0] and not move.posted_before and move.date:
                # In the form view, we need to compute a default sequence so that the user can edit
                # it. We only check the first move as an approximation (enough for new in form view)
                pass
            elif (move.name and move.name != '/') or move.state != 'posted':
                try:
                    if not move.posted_before:
                        move._constrains_date_sequence()
                    # Has already a name or is not posted, we don't add to a batch
                    continue
                except ValidationError:
                    # Has never been posted and the name doesn't match the date: recompute it
                    pass
            group = grouped[journal_key(move)][date_key(move)]
            if not group['records']:
                # Compute all the values needed to sequence this whole group
                move._set_next_sequence()
                group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
                group['reset'] = move._deduce_sequence_number_reset(move.name)
            group['records'] += move

        # Fusion the groups depending on the sequence reset and the format used because `seq` is
        # the same counter for multiple groups that might be spread in multiple months.
        final_batches = []
        for journal_group in grouped.values():
            journal_group_changed = True
            for date_group in journal_group.values():
                if (
                    journal_group_changed
                    or final_batches[-1]['format'] != date_group['format']
                    or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
                ):
                    final_batches += [date_group]
                    journal_group_changed = False
                elif date_group['reset'] == 'never':
                    final_batches[-1]['records'] += date_group['records']
                elif (
                    date_group['reset'] == 'year'
                    and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
                ):
                    final_batches[-1]['records'] += date_group['records']
                else:
                    final_batches += [date_group]

        # Give the name based on previously computed values
        for batch in final_batches:
            for move in batch['records']:
                move.name = batch['format'].format(**batch['format_values'])
                batch['format_values']['seq'] += 1
            batch['records']._compute_split_sequence()

        self.filtered(lambda m: not m.name).name = '/'


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    account_payment_id = fields.Many2one('account.payment', 'PDC Payment')

    def _compute_amount_fields(self, amount, src_currency, company_currency):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        date = self.env.context.get('date') or fields.Date.today()
        company = self.env.context.get('company_id')
        company = self.env['res.company'].browse(company) if company else self.env.user.company_id
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            amount = src_currency._convert(amount, company_currency, company, date)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        return debit, credit, amount_currency, currency_id


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_default_journal(self):
        ''' Retrieve the default journal for the account.payment.
        /!\ This method will not override the method in 'account.move' because the ORM
        doesn't allow overriding methods using _inherits. Then, this method will be called
        manually in 'create' and 'new'.
        :return: An account.journal record.
        '''

        return False

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1 or len(counterpart_lines) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal entry must always contains:\n"
                        "- one journal item involving the outstanding payment/receipts account.\n"
                        "- one journal item involving a receivable/payable account.\n"
                        "- optional journal items, all sharing the same account.\n\n"
                    ) % move.display_name)

                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, all the write-off journal items must share the same account."
                    ) % move.display_name)

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same currency."
                    ) % move.display_name)

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same partner."
                    ) % move.display_name)

                # if counterpart_lines.account_id.user_type_id.type == 'receivable':
                #     partner_type = 'customer'
                # else:
                #     partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    # 'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def update_paid_date(self):
        self._cr.execute("""UPDATE account_move 
set date=account_payment.paid_date + interval '4' HOUR * 1
from account_payment
where account_move.id = account_payment.journal_entry_id and account_payment.id in (14833,
9653,
7173,
6922,
15733,
6917,
15580,
15196,
14762,
14711,
14710,
14162,
14678,
14677,
7172
)
""")
        self._cr.commit()
        self._cr.execute("""UPDATE account_move_line 
set date=account_payment.paid_date + interval '4' HOUR * 1
from account_payment,account_move
where account_move.id = account_payment.journal_entry_id and account_move.id = account_move_line.move_id and account_payment.id in (14833,
9653,
7173,
6922,
15733,
6917,
15580,
15196,
14762,
14711,
14710,
14162,
14678,
14677,
7172
)
""")
        self._cr.commit()

    def update_ninja_data(self):
        self._cr.execute("update mail_followers set channel_id = 19 where channel_id is not null;")
        self._cr.commit()
        self._cr.execute("update account_tax_template set chart_template_id=1")
        self._cr.commit()
        self._cr.execute("delete from account_tax_report_line_tags_rel")
        self._cr.commit()
        self._cr.execute("update account_tax_template set tax_group_id=2 where tax_group_id>2")
        self._cr.commit()
        self._cr.execute("delete from account_tax_repartition_minus_report_line")
        self._cr.commit()

    def create_account_payment(self):
        payments = self.env['account.payment'].search(
            [('payment_type', '=', 'outbound'), ('move_id.state', '=', 'cancel'), ('partner_id', '!=', False)])
        for payment in payments:
            filter = payment.move_id.line_ids.filtered(
                lambda move: move.account_id == payment.partner_id.property_account_payable_id and move.debit == 0)
            if filter:
                line_vals = []
                if payment.payment_type == 'outbound':
                    print("outbound")
                    print(payment.id)
                    print(payment.old_journal_id.payment_credit_account_id.id)
                    print(payment.partner_id.property_account_payable_id.id)
                    line_vals.append({
                        'name': _('Payments'),
                        'debit': payment.amount or 0,
                        'asset_project_id': payment.asset_project_id.id,
                        'property_id': payment.property_id.id,
                        'credit': 0,
                        'date': payment.old_payment_date,
                        'account_id': payment.partner_id.property_account_payable_id.id,
                        'partner_id': payment.partner_id.id or None,
                        'currency_id': self.env.company.currency_id.id,
                    })
                    line_vals.append({
                        'name': _('Payments'),
                        'debit': 0,
                        'asset_project_id': payment.asset_project_id.id,
                        'property_id': payment.property_id.id,
                        'credit': payment.amount or 0,
                        'date': payment.old_payment_date,
                        'account_id': payment.old_journal_id.payment_credit_account_id.id,
                        'partner_id': payment.partner_id.id or None,
                        'currency_id': self.env.company.currency_id.id,
                    })

                    move_id = self.env['account.move'].sudo().create({
                        'currency_id': self.env.company.currency_id.id,
                        'move_type': 'entry',
                        'asset_project_id': payment.asset_project_id.id,
                        'partner_id': payment.partner_id.id,
                        'property_id': payment.property_id.id,
                        'journal_id': payment.old_journal_id.id,
                        'date': payment.old_payment_date,
                        'ref': "Payments",
                        'line_ids': [(0, 0, line) for line in line_vals],
                    })
                    move_id.button_cancel()
                    payment.move_id = move_id.id

    @api.depends('is_internal_transfer')
    def _compute_partner_id(self):
        for pay in self:
            if pay.is_internal_transfer:
                pay.partner_id = pay.journal_id.company_id.partner_id
            # elif pay.partner_id == pay.journal_id.company_id.partner_id:
            #     pay.partner_id = False
            else:
                pay.partner_id = pay.partner_id

    @api.depends('journal_id', 'payment_method_code')
    def _compute_check_number(self):
        return

    def _inverse_check_number(self):
        return

    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        domain="[]",
        check_company=True, tracking=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer/Vendor",
        store=True, readonly=False, ondelete='restrict',
        compute='_compute_partner_id',
        domain="['|', ('parent_id','=', False), ('is_company','=', True)]",
        check_company=True, tracking=True)

    posting_ledger = fields.Many2one('account.journal','Posting Ledger', tracking=True)
    old_name = fields.Char('Old Sequence')
    old_journal_id = fields.Many2one('account.journal',string='Old Journal_id', help='This is old Journal Id')
    old_payment_date = fields.Date('Payment Date')
    # booking_id = fields.Many2one('crm.booking', string="Booking")
    confirmed_user_id = fields.Many2one('res.users', 'Confirmed User', tracking=True)
    collection_type_id = fields.Many2one('collection.type', string="Collection Type", tracking=True)
    spa_id = fields.Many2one('sale.order', 'SPA', tracking=True)
    spa_payment_id = fields.Many2one('sale.order', 'SPA', tracking=True)
    account_holder_name = fields.Text('A/c Holder', readonly=False, states={'posted': [('readonly', True)]})
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]", tracking=True)
    property_id = fields.Many2one('account.asset.asset', string='Property', tracking=True)
    rental_id = fields.Many2one('account.analytic.account', string='Rental Tenancy')

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    @api.depends('oqood_amount', 'admin_amount')
    def _get_net_amount(self):
        for rec in self:
            rec.nets_amount = rec.amount - rec.oqood_amount - rec.admin_amount

    oqood_amount = fields.Float(string="Oqood Amount", tracking=True)
    admin_amount = fields.Float(string="Admin Amount", tracking=True)
    nets_amount = fields.Float(string="Net Amount", compute='_get_net_amount')
    collection_team_id = fields.Many2one('collections.team', string="Collection Team", tracking=True)
    officer_id = fields.Many2one('res.users', 'Collection Officer', tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('under_accounts_verification', 'Under Accounts Verification'),
         ('under_review', 'Under Review'),
         ('under_approval', 'Under Approval'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected'),
         ('proforma', 'Pro-forma'),
         ('pending', 'Pending for Collection'),
         ('collected', 'Collected'),
         ('outsourced', 'Withdraw'),
         ('stale', 'Stale'),
         ('replaced', 'Replaced'),
         ('hold', 'Hold'),
         ('deposited', 'Deposited'),
         ('posted', 'Posted'),
         ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled'),
         ('refused', 'Bounced'),
         ], 'Status', readonly=True, default='draft', tracking=True)

    journal_entry_id = fields.Many2one('account.move', 'Journal Pending Entry Associate')
    move_entry_ids = fields.One2many(related='journal_entry_id.line_ids', string='Journal Pending',
                                     readonly=True)
    redeposit_entry = fields.Many2one('account.move', 'Journal Redeposit Entry')
    journal_rejected_entry = fields.Many2one('account.move', 'Journal Rejected Entry Associate')
    move_rejected_ids = fields.One2many(related='journal_rejected_entry.line_ids', string='Journal Rejected',
                                        readonly=True)

    journal_pending_entry = fields.Many2one('account.move', 'Journal Pending Entry Associate')
    move_pending_ids = fields.One2many(related='journal_pending_entry.line_ids', string='Journal Pending',
                                       readonly=True)
    journal_collected_entry = fields.Many2one('account.move', 'Journal Collected Entry Associate')
    move_collected_ids = fields.One2many(related='journal_collected_entry.line_ids', string='Journal Collected',
                                         readonly=True)
    journal_posted_entry = fields.Many2one('account.move', 'Journal Posted Entry Associate')
    move_posted_ids = fields.One2many(related='journal_posted_entry.line_ids', string='Journal Posted', readonly=True)

    journal_outsourced_entry = fields.Many2one('account.move', 'Journal Withdraw Entry Associate')
    move_outsourced_ids = fields.One2many(related='journal_outsourced_entry.line_ids', string='Journal Withdraw',
                                          readonly=True)
    journal_bank_entry = fields.Many2one('account.move', 'Journal Bank Entry Associate')
    move_bank_ids = fields.One2many(related='journal_bank_entry.line_ids', string='Journal Banks', readonly=True)
    journal_deposited_entry = fields.Many2one('account.move', 'Journal Deposited Entry Associate')
    move_deposited_ids = fields.One2many(related='journal_deposited_entry.line_ids', string='Journal Deposited',
                                         readonly=True)
    collection_date = fields.Datetime('Collection Date', tracking=True)
    maturity_date = fields.Datetime('Maturity Date', tracking=True)
    posting_date = fields.Datetime('Deposit Date', tracking=True)
    paid_date = fields.Datetime('Posting Date', tracking=True)
    bounced_date = fields.Date('Bounced Date', tracking=True)
    check_number = fields.Char('Check Number', tracking=True)
    agreed_term = fields.Char('Agreed Term')
    reference = fields.Char('Payment Ref.', size=64, help="Transaction reference number.", tracking=True)

    bounced_move_deposited_ids = fields.One2many('account.move.line', 'account_payment_id',
                                                 string='Journal Deposited Bounced',
                                                 readonly=True, tracking=True, )
    re_deposit = fields.Integer('Re-Deposits', tracking=True)
    rd1_deposit_date = fields.Date('RD1 Deposit Date', tracking=True)
    rd1_posting_date = fields.Date('RD1 Posting Date', tracking=True)
    rd1_bounced_date = fields.Date('RD1 Bounced Date', tracking=True)
    rd2_deposit_date = fields.Date('RD2 Deposit Date', tracking=True)
    rd2_posting_date = fields.Date('RD2 Posting Date', tracking=True)
    rd2_bounced_date = fields.Date('RD2 Bounced Date', tracking=True)
    approval_from_ids = fields.Many2many('res.users', 'payment_approval_from_rel', 'payment_approval_id', 'user_id',
                                         'Approval From')
    visibility_check = fields.Boolean('Approval Visibility', compute='_compute_approval_visibility')


    def _compute_approval_visibility(self):
        for rec in self:
            if set(rec.approval_from_ids.ids) & set(self.env.user.ids):
                rec.visibility_check = True
            else:
                rec.visibility_check = False

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            if self.journal_id.type == 'pdc':
                self.update({'chk': True})
                self.update({'other_payment': True})
            else:
                self.update({'chk': False})
                self.update({'other_payment': False})

    # @api.onchange('chk')
    # def _onchange_chk(self):
    #     if self.chk:
    #         self.update({'other_payment': True})
    #     else:
    #         self.update({'other_payment': False})

    def submit_accounts_verification(self):
        if not self.name or self.name == "/":
            self.action_create_sequence()
        for rec in self:
            user = self.env.user
            if user.receipt_confirmation_limit:
                total = 0
                total2 = 0
                for line in user.receipts_confirmed_ids:
                    total += line.amount
                for line1 in rec.collection_line:
                    total2 += line1.amount
                total_to_confirm = total + total2
                if total_to_confirm > user.receipt_confirmation_limit:
                    raise ValidationError(
                        'Your amount limit exceed from validation limit, please contact administrator')
            voucher = rec
            if not voucher.name or voucher.name == "/":
                # Use the right sequence to set the name
                if voucher.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if voucher.partner_type == 'customer':
                        if voucher.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if voucher.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if voucher.partner_type == 'supplier':
                        if voucher.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if voucher.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                voucher.name = self.env['ir.sequence'].with_context(ir_sequence_date=voucher.date).next_by_code(
                    sequence_code)

            rec.write({'state': 'under_accounts_verification'})
        return True


    salesperson_id = fields.Many2one('res.users', 'SalesPerson',
                                     tracking=True)
    owner_ids = fields.Many2many('res.users', 'payment_owner_rel', 'payment_id', 'user_id', 'Owner',
                                 compute='get_owner', store=True, )
    accounting_ledger_id = fields.Many2one('account.account', 'Accounting Ledger')

    bank = fields.Many2one('res.partner.bank', 'Bank', help='This bank indicate the name of the bank of check')
    bank_issued_check = fields.Many2one('res.bank', 'Bank',
                                        help='This bank indicate the name of the bank of check')
    bank_deposit = fields.Many2one('res.partner.bank', 'Bank where the check is deposit/cashed',
                                   help='This bank indicate the name of the bank which the check is deposit and cashed')
    # invoice_id = fields.Many2one('account.invoice', 'Invoice', readonly=True,
    #                              states={'draft': [('readonly', False)], 'pending': [('readonly', False)]}, )
    chk = fields.Boolean('PDC Check')
    other_payment = fields.Boolean('Other Payment')

    #
    remarks = fields.Text('Remarks', readonly=False, states={'posted': [('readonly', True)]})
    mobile = fields.Char('Mobile', related='partner_id.mobile', readonly=True)
    email = fields.Char('Email', related='partner_id.email', readonly=True)
    old_number = fields.Char('Old Number', help='This is old data number')
    hold_date = fields.Date('Hold Date')
    amount_due = fields.Monetary(
        comodel_name='res.partner',
        related='partner_id.credit',
        readonly=True,
        default=0.0,
        help='Display Due amount of Customer')

    @api.onchange('accounting_ledger_id')
    def _onchange_accounting_ledger(self):
        if self.accounting_ledger_id:
            self.destination_account_id = self.accounting_ledger_id.id

    def action_settle(self):
        self.write({'state': 'settle'})

    def action_stale(self):
        for rec in self:
            rec.write({'state': 'stale'})

    def submit_for_review(self):
        self.write({'state': 'under_review'})

    def submit_for_approval(self):
        self.write({'state': 'under_approval'})

    def action_reject(self):
        # self.write({'state': 'rejected'})
        for rec in self:
            if rec.journal_id.type == 'pdc':
                list_moves = []
                if rec.journal_entry_id:
                    list_moves.append(rec.journal_entry_id.id)
                if rec.journal_posted_entry:
                    list_moves.append(rec.journal_posted_entry.id)
                if rec.journal_rejected_entry:
                    list_moves.append(rec.journal_rejected_entry.id)
                if rec.journal_outsourced_entry:
                    list_moves.append(rec.journal_outsourced_entry.id)
                if rec.journal_bank_entry:
                    list_moves.append(rec.journal_bank_entry.id)
                account_move_line_ids = self.env['account.move.line'].search([('payment_id', '=', rec.id)])
                for line in account_move_line_ids:
                    list_moves.append(line.move_id.id)
                account_move_ids = self.env['account.move'].search([('id', 'in', list_moves)])
                if account_move_ids:
                    for ac_move_id in account_move_ids:
                        ac_move_id.button_cancel()
                rec.write({'state': 'rejected'})
            else:
                if rec.journal_entry_id:
                    # if rec.invoice_ids:
                    #     move.line_ids.remove_move_reconcile()
                    rec.journal_entry_id.button_cancel()
                rec.write({'state': 'rejected'})

    def cron_rejcted_jv_cancel(self):
        payments = self.env['account.payment'].search([('state','=','rejected')])
        # self.write({'state': 'rejected'})
        for rec in payments:
            if rec.journal_id.type == 'pdc':
                list_moves = []
                if rec.journal_entry_id:
                    list_moves.append(rec.journal_entry_id.id)
                if rec.journal_posted_entry:
                    list_moves.append(rec.journal_posted_entry.id)
                if rec.journal_rejected_entry:
                    list_moves.append(rec.journal_rejected_entry.id)
                if rec.journal_outsourced_entry:
                    list_moves.append(rec.journal_outsourced_entry.id)
                if rec.journal_bank_entry:
                    list_moves.append(rec.journal_bank_entry.id)
                account_move_line_ids = self.env['account.move.line'].search([('payment_id', '=', rec.id)])
                for line in account_move_line_ids:
                    list_moves.append(line.move_id.id)
                account_move_ids = self.env['account.move'].search([('id', 'in', list_moves)])
                if account_move_ids:
                    for ac_move_id in account_move_ids:
                        ac_move_id.button_cancel()
            else:
                if rec.journal_entry_id:
                    # if rec.invoice_ids:
                    #     move.line_ids.remove_move_reconcile()
                    rec.journal_entry_id.button_cancel()

    def action_approve(self):
        self.write({'state': 'approved'})

    def check_outsourced(self):
        self.write({'state': 'replaced'})

    def check_replaced(self):
        self.write({'state': 'replaced'})

    def button_hold(self):
        self.write({'state': 'hold'})

    def pdc_roolback(self):
        self.write({'state': 'collected'})

    def print_report(self):
        return self.env.ref('account.action_report_payment_receipt').report_action(self, data=None)

    def action_draft(self):
        for line in self:
            line.move_id.button_draft()
            line.write({'state': 'draft'})

    def action_draft_to_cancel(self):
        self.write({'state': 'cancelled'})
        self.move_id.button_cancel()

    def replace_cancel_state(self):
        cancel_ids = self.env['account.payment'].search([])
        for rec in cancel_ids:
            if rec.state == 'cancel':
                rec.state = 'cancelled'

    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        for line in self.move_id.line_ids:
            if line.account_id in (
                    self.journal_id.default_account_id,
                    self.journal_id.payment_debit_account_id,
                    self.journal_id.payment_credit_account_id,
                    self.bank_deposit.journal_id.payment_debit_account_id,
                    self.bank_deposit.journal_id.payment_credit_account_id,
                    self.posting_ledger.payment_debit_account_id,
                    self.posting_ledger.payment_credit_account_id,
            ):
                liquidity_lines += line
            elif line.account_id.internal_type in ('receivable', 'payable','liquidity','other') or line.partner_id == line.company_id.partner_id:
                counterpart_lines += line
            else:
                writeoff_lines += line

        return liquidity_lines, counterpart_lines, writeoff_lines

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountPayment, self).create(vals_list)
        # if res.name:
            # old_name = res.name
            # name_split = old_name.split('/')
            # if name_split[0] != res.journal_id.code:
            #     res.name = old_name.replace(name_split[0], res.journal_id.code)
            # old_name = res.name
            # name_split = old_name.split('/')
            # if name_split[0] != res.journal_id.code:
            #     highest_name = res.move_id._get_last_sequence()
            #     second_split = highest_name.split('/')
            #     if name_split[-1] <= second_split[-1]:
            #         new_num = str(int(second_split[-1]) + 1).zfill(len(second_split[-1]))
            #         second_name = old_name.replace(name_split[0], res.journal_id.code)
            #         res.name = second_name.replace(nam        e_split[-1], str(new_num))
        for line in res:
            if line.move_id and line.chk:
                line.move_id.button_cancel()
        return res

    def cancel(self):
        for rec in self:
            if rec.journal_id.type == 'pdc':
                list_moves = []
                if rec.journal_entry_id:
                    list_moves.append(rec.journal_entry_id.id)
                if rec.journal_posted_entry:
                    list_moves.append(rec.journal_posted_entry.id)
                if rec.journal_rejected_entry:
                    list_moves.append(rec.journal_rejected_entry.id)
                if rec.journal_outsourced_entry:
                    list_moves.append(rec.journal_outsourced_entry.id)
                if rec.journal_bank_entry:
                    list_moves.append(rec.journal_bank_entry.id)
                account_move_line_ids = self.env['account.move.line'].search([('payment_id', '=', rec.id)])
                for line in account_move_line_ids:
                    list_moves.append(line.move_id.id)
                account_move_ids = self.env['account.move'].search([('id', 'in', list_moves)])
                if account_move_ids:
                    for ac_move_id in account_move_ids:
                        ac_move_id.button_cancel()
                        ac_move_id.unlink()
                rec.write({'state': 'cancelled'})
            else:
                for move in rec.move_line_ids.mapped('move_id'):
                    # if rec.invoice_ids:
                    #     move.line_ids.remove_move_reconcile()
                    move.button_cancel()
                    move.unlink()
                rec.state = 'cancelled'


    def action_post(self):
        ''' draft -> posted '''
        # if not self.name or self.name == "/":
        #     self.action_create_sequence()
        self.move_id._post(soft=False)
        self.state = 'posted'
        self.journal_entry_id = self.move_id.id
        if self.amount >= 5000.0 and self.journal_id.type == 'cash' and self.partner_type == 'customer':  # and self.receipt_id.journal_id.subtype == 'receivable' and self.receipt_id.journal_id.type == 'cash':
            print("this is sms cash")
            sms_env = self.env['partner.sms.send']
            data = self.env['sms.smsclient'].search([('name', '=', 'SAMANA')])
            mr = self.env['mail.recipients'].search([('name', '=', 'Cash Payment sms')])
            sender = mr.user_ids
            # sender = self.env['res.users'].search(
            #     [('login', 'in', ['baig@globalmigration.co.uk'])])
            print(sender)
            message = "Accounts - Cash Received By "+self.env.user.name+ "\nAED "+str('{:,.2f}'.format(self.amount)) + "\nFrom "+ self.partner_id.name + "\nDate "+ str(self.date.strftime('%d-%m-%Y'))
            print(message)
            for line in sender:
                if line.mobile:
                    if data:
                        # if not self._check_permissions():
                        #     raise UserError(_('You have no permission to access %s') % (data.name,))
                        url = data.url
                        name = url
                        if data.method == 'http':
                            prms = {}
                            for p in data.property_ids:
                                if p.type == 'user':
                                    prms[p.name] = p.value
                                elif p.type == 'password':
                                    prms[p.name] = p.value
                                elif p.type == 'to':
                                    prms[p.name] = line.mobile
                                elif p.type == 'sms':
                                    prms[p.name] = data.text
                                elif p.type == 'extra':
                                    prms[p.name] = p.value
                                elif p.type == 'type':
                                    prms[p.name] = p.value
                                elif p.type == 'source':
                                    prms[p.name] = p.value
                            # prms['type'] = 0
                            # prms['source'] = 'SD'
                            prms['message'] = message
                            prms['destination'] = line.mobile[1:]

                            params = parse.urlencode(prms)
                            name = url + params
                            # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=GMS&message=dfdf&destination=923136340004"
                        # urlopen(
                        # "http://sms.rmlconnect.net/bulksms/bulksms?username=GMSUAE&dlr=1&password=asdf1234&type=0&source=SD&message=newmessage&destination=923136340004")
                        queue_obj = self.env['sms.smsclient.queue']
                        vals = {
                            'name': name,
                            'gateway_id': data.id,
                            'state': 'draft',
                            'mobile': line.mobile,
                            'msg': prms['message'],
                            # 'validity': data.validity,
                            # 'classes': data.classes1,
                            # 'deffered': data.deferred,
                            # 'priorirty': data.priority,
                            # 'coding': data.coding,
                            # 'tag': data.tag,
                            # 'nostop': data.nostop1,
                        }
                        send_sms = queue_obj.create(vals)
                        sms = self.env["sms.smsclient"]
                        sms._check_queue()

    def action_cancel(self):
        ''' draft -> cancelled '''
        self.move_id.button_cancel()
        self.state = 'cancelled'

    def action_pending(self):
        self.state = 'pending'

    def rejected_check(self):
        self.env.context = dict(self.env.context)
        self.env.context.update({'bounce_payment':True})
        if self.redeposit_entry:
            if self.re_deposit == 1:
                if not self.rd1_bounced_date:
                    raise UserError('Please select RD1 bounce date')
                date = self.rd1_bounced_date
            if self.re_deposit == 2:
                if not self.rd2_bounced_date:
                    raise UserError('Please select RD2 bounce date')
                date = self.rd2_bounced_date
            move = self.redeposit_entry.ids
        else:
            if not self.bounced_date:
                raise UserError('Please select bounce date')
            move = self.move_id.ids
            date = self.bounced_date

        if not self.bounced_date:
            raise UserError('Please select bounce date')
        reverse_entry = self.env['account.move.reversal'].create({
            'date_mode': 'custom',
            'refund_method': 'cancel',
            'date': date or datetime.date.today(),
            'move_ids': [(6, 0, move)]
        })
        entry = reverse_entry.reverse_moves()
        if entry.get('res_id'):
            self.journal_rejected_entry = entry.get('res_id')
            # self.journal_rejected_entry._post(soft=False)
        else:
            raise UserError('Reverse Entry id Not Generated')
        self.write({'state': 'refused'})

    def button_collected(self):
        if not self.collection_date:
            self.collection_date = fields.Datetime.now()
        if self.journal_rejected_entry:
            self.re_deposit += 1
        if not self.name or self.name == "/":
            self.action_create_sequence()
        self.write({'state': 'collected'})

    def action_pay(self):
        self.write({'state': 'deposited'})

    def action_pending_to_collected(self):
        res = {}
        # BEGIN VOUCHER CUSTOMIZATION
        for voucher in self:
            if not voucher.collection_date:
                self.write({'collection_date': datetime.datetime.now()})
        return res

    def update_payment(self, vals_list):
        # OVERRIDE
        if self.collection_type_id.id == 19:
            if self.chk and not self.posting_ledger:
                raise UserError(_("Please Select Posting Ledger."))
            if self.chk and not self.posting_ledger.payment_debit_account_id.id:
                raise UserError(_("Accounts not configured on selected posting ledger journal."))
        else:
            if self.chk and not self.bank_deposit:
                raise UserError(_("Bank where the check is deposit/cashed is not selected."))
            if self.chk and not self.bank_deposit.journal_id:
                raise UserError(_("Journal is not associated with selected bank."))
            if self.chk and not self.bank_deposit.journal_id.payment_debit_account_id.id:
                raise UserError(_("Accounts not configured on selected bank journal."))
        write_off_line_vals_list = []

        for vals in vals_list:

            # Hack to add a custom write-off line.
            write_off_line_vals_list.append(vals.pop('write_off_line_vals', None))

            # Force the move_type to avoid inconsistency with residual 'default_move_type' inside the context.
            vals['move_type'] = 'entry'

            # Force the computation of 'journal_id' since this field is set on account.move but must have the
            # bank/cash type.
            if 'journal_id' not in vals:
                vals['journal_id'] = self._get_default_journal().id

            # Since 'currency_id' is a computed editable field, it will be computed later.
            # Prevent the account.move to call the _get_default_currency method that could raise
            # the 'Please define an accounting miscellaneous journal in your company' error.
            if 'currency_id' not in vals:
                journal = self.env['account.journal'].browse(vals['journal_id'])
                vals['currency_id'] = journal.currency_id.id or journal.company_id.currency_id.id

        payments = self

        for i, pay in enumerate(payments):
            write_off_line_vals = write_off_line_vals_list[i]

            # Write payment_id on the journal entry plus the fields being stored in both models but having the same
            # name, e.g. partner_bank_id. The ORM is currently not able to perform such synchronization and make things
            # more difficult by creating related fields on the fly to handle the _inherits.
            # Then, when partner_bank_id is in vals, the key is consumed by account.payment but is never written on
            # account.move.
            to_write = {'payment_id': pay.id}
            for k, v in vals_list[i].items():
                if k in self._fields and self._fields[k].store and k in pay.move_id._fields and pay.move_id._fields[
                    k].store:
                    to_write[k] = v

            if 'line_ids' not in vals_list[i]:
                to_write['line_ids'] = [(0, 0, line_vals) for line_vals in
                                        pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)]
            for l in to_write['line_ids']:
                if l[2]['debit']:
                    if self.collection_type_id.id == 19:
                        l[2]['account_id'] = self.posting_ledger.payment_debit_account_id.id
                    else:
                        l[2]['account_id'] = self.bank_deposit.journal_id.payment_debit_account_id.id
            if not to_write.get('journal_id'):
                to_write.update({'journal_id':self.journal_id.id})
            move = self.env['account.move'].create(to_write)
            for data in move.line_ids:
                data.account_payment_id = payments.id

        return move

    def voucher_posted_inbound(self):
        if self.collection_type_id.id == 19:
            if self.chk and not self.posting_ledger:
                raise UserError(_("Please Select Posting Ledger."))
            if self.chk and not self.posting_ledger.payment_debit_account_id.id:
                raise UserError(_("Accounts not configured on selected posting ledger journal."))
        else:
            if self.chk and not self.bank_deposit:
                raise UserError(_("Bank where the check is deposit/cashed is not selected."))
            if self.chk and not self.bank_deposit.journal_id:
                raise UserError(_("Journal is not associated with selected bank."))
            if self.chk and not self.bank_deposit.journal_id.payment_debit_account_id.id:
                raise UserError(_("Accounts not configured on selected bank journal."))
        if self.journal_entry_id and (self.create_date > datetime.datetime.strptime('2021-08-15', '%Y-%m-%d') or self.re_deposit > 0):
        # if self.journal_entry_id:
            vals = [{'name': False, 'payment_type': 'inbound', 'partner_type': 'customer',
                     'collection_type_id': self.collection_type_id.id,
                     'partner_id': self.partner_id.id, 'journal_id': self.journal_id.id,
                     'destination_account_id': self.destination_account_id.id, 'amount': self.amount,
                     'currency_id': self.currency_id.id,
                     'is_internal_transfer': self.is_internal_transfer, 'check_number': self.check_number,
                     'maturity_date': self.maturity_date, 'collection_date': self.collection_date,
                     'account_holder_name': self.account_holder_name, 'oqood_amount': self.oqood_amount,
                     'admin_amount': self.admin_amount, 'chk': self.chk,
                     'journal_entry_id': False, 'other_payment': False, 'date': self.date, 'reference': self.reference,
                     'spa_id': self.spa_id.id, 'asset_project_id': self.asset_project_id.id,
                     'property_id': self.property_id.id, 'remarks': self.remarks, 'posting_date': self.posting_date,
                     'paid_date': self.paid_date, 'bounced_date': self.bounced_date, 'officer_id': self.officer_id.id,
                     'hold_date': self.hold_date, 'edi_document_ids': [],
                     'rd1_deposit_date': False, 'rd1_posting_date': False, 'rd1_bounced_date': False,
                     'rd2_deposit_date': False, 'rd2_posting_date': False, 'rd2_bounced_date': False,
                     'message_follower_ids': [], 'activity_ids': [], 'message_ids': []}]
            move = self.update_payment(vals)
            self.redeposit_entry = move.id
            # self.move_id = move.id
            if move:
                for line in move.line_ids:
                    if self.rd1_posting_date or self.rd2_posting_date:
                        if self.re_deposit == 1:
                            line.date = self.rd1_posting_date
                        if self.re_deposit == 2:
                            line.date = self.rd2_posting_date
                move.action_post()

            self.write({'state': 'posted'})
            # voucher = self
            # if voucher.journal_id.entry_posted:
            #     self.pool.get('account.move').post(move_pay_id)
            return True
        if self.move_id.line_ids:
            self.move_id.button_draft()
            if self.collection_type_id.id == 19:
                debit_account_id = self.posting_ledger.payment_debit_account_id.id
            else:
                debit_account_id = self.bank_deposit.journal_id.payment_debit_account_id.id
            for line in self.move_id.line_ids:
                if not self.paid_date:
                    raise UserError(_("Posting Date not set"))
                line.date = self.paid_date
                if line.debit:
                    line.update({'account_id': debit_account_id})
                    print('Done')
        self.move_id._post(soft=False)
        self.journal_entry_id = self.move_id.id
        self.write({'state': 'posted'})

    def voucher_posted_outbound(self):
        if self.collection_type_id.id == 19:
            if self.chk and not self.posting_ledger:
                raise UserError(_("Please Select Posting Ledger."))
            if self.chk and not self.posting_ledger.payment_credit_account_id.id:
                raise UserError(_("Accounts not configured on selected posting ledger journal."))
        else:
            if self.chk and not self.bank_deposit:
                raise UserError(_("Bank where the check is deposit/cashed is not selected."))
            if self.chk and not self.bank_deposit.journal_id:
                raise UserError(_("Journal is not associated with selected bank."))
            if self.chk and not self.bank_deposit.journal_id.payment_credit_account_id:
                raise UserError(_("Accounts not configured on selected bank journal."))

        if self.move_id and self.move_id.line_ids:
            self.move_id.button_draft()
            if self.collection_type_id.id == 19:
                credit_account_id = self.posting_ledger.payment_credit_account_id.id
            else:
                credit_account_id = self.bank_deposit.journal_id.payment_credit_account_id.id
            for line in self.move_id.line_ids:
                if not self.paid_date:
                    raise UserError(_("Posting Date not set"))
                line.date = self.paid_date
                if line.credit:
                    line.update({'account_id': credit_account_id})
                    print('Done')
        self.move_id._post(soft=False)
        self.journal_entry_id = self.move_id.id
        self.write({'state': 'posted'})




    def action_create_sequence(self):
        voucher = self
        if not voucher.name:
            # Use the right sequence to set the name
            if voucher.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if voucher.partner_type == 'customer':
                    if voucher.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if voucher.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if voucher.partner_type == 'supplier':
                    if voucher.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if voucher.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            voucher.name = self.env['ir.sequence'].with_context(ir_sequence_date=voucher.date).next_by_code(
                sequence_code)
            if not voucher.name and voucher.payment_type != 'transfer':
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))


# class SaleOrderReportProforma(models.AbstractModel):
#     _name = 'report.account.report_payment_receipt'
#     _description = 'Receipt Report'
#
#     def _get_report_values(self, docids, data=None):
#         # res = super(SaleOrderReportProforma, self)._get_report_values(self, docids, data=None)
#         docs = self.env['account.payment'].browse(docids)
#         for doc in docs:
#             if doc.state in ['draft', 'cancelled']:
#                 raise UserError(_("Please, Report is not available in draft and cancelled state."))
#         else:
#             return {
#                 'doc_ids': docids,
#                 'doc_model': 'account.payment',
#                 'docs': docs,
#                 'report_type': data.get('report_type') if data else '',
#             }


class ResUsers(models.Model):
    _inherit = 'res.users'

    receipt_confirmation_limit = fields.Float('Receipt Confirmation Limit')
    receipts_confirmed_ids = fields.Many2many('account.payment', 'payment_user_confirmed_rel', 'payment_id', 'user_id',
                                              compute="compute_submited_receipts",
                                              domain="[('payment_type','=','inbound')]", string="Confirmed Receipts")

    def compute_submited_receipts(self):
        for rec in self:
            reciept = rec.env['account.payment'].search(
                [('confirmed_user_id', '=', rec.id), ('state', '=', 'under_accounts_verification'),
                 ('payment_type', '=', 'inbound')])
            rec.receipts_confirmed_ids = [(6, 0, reciept.ids)]
