# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(selection_add=[
    ('under_review', 'Under Review'),
    ('under_approval', 'Under Approval'),
    ('rejected', 'Rejected')
    ], ondelete={'rejected': 'set default', 'under_review': 'set default', 'under_approval': 'set default'})
    invoice_type = fields.Many2one('invoice.type', 'Invoice Type')
    schedule_id = fields.Many2one('sale.rent.schedule', 'Schedule')
    property_id = fields.Many2one('account.asset.asset',
                                  string='Property',
                                  help='Property Name.', tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset',
                                       string='Project',
                                       help='Property Name.', tracking=True)

    # @api.model
    # def cron_payment_state1(self,iv=False):
    #     if iv:
    #         inv = self.search([('move_type','in',['in_invoice', 'out_invoice']),('state','=', 'posted'),('id','=',iv)])
    #     else:
    #         inv = self.search([('move_type','in',['in_invoice', 'out_invoice']),('state','=', 'posted')])
    #     for move in inv:
    #         if move.amount_total - move.amount_residual == move.amount_total:
    #             move.payment_state = 'paid'
    #         if move.amount_residual != 0 and move.amount_residual < move.amount_total and move.amount_total - move.amount_residual < move.amount_total:
    #             move.payment_state = 'partial'
    #         if move.amount_total - move.amount_residual == 0:
    #             move.payment_state = 'not_paid'

    @api.model
    def cron_payment_state(self):
        query = """UPDATE account_move
                SET payment_state = CASE
                                    WHEN amount_total - amount_residual = amount_total THEN 'paid'
                                    WHEN amount_residual !=0 AND amount_residual < amount_total  AND amount_total - amount_residual < amount_total THEN 'partial'
                                    WHEN amount_total - amount_residual = 0 THEN 'not_paid'
                                END
                WHERE move_type in ('in_invoice', 'out_invoice') AND state='posted'"""
        self._cr.execute(query)
        self._cr.commit()

    @api.model
    def cron_jv_post(self):
        _logger.info('query 1 running =================================== :')
        query = """UPDATE account_move SET state = 'posted'
            FROM account_journal
            where account_journal.id=account_move.journal_id AND account_move.move_type='entry' AND account_journal.type = 'cash' AND account_move.date<'01/07/2019' AND account_move.state='draft'"""
        self._cr.execute(query)
        self._cr.commit()

    @api.model
    def cron_jv_post_try(self):
        _logger.info('query 1 running =================================== :')
        try:
            query = """UPDATE account_move SET state = 'posted'
                FROM account_journal
                where account_journal.id=account_move.journal_id AND account_move.move_type='entry' AND account_journal.type = 'cash' AND account_move.date<'01/07/2019' AND account_move.state='draft'"""
            self._cr.execute(query)
            self._cr.commit()
        except Exception as e:
            _logger.info("---Exception raised : %r while sending OTP", e)

    @api.model
    def cron_jv_post_cash(self):
        _logger.info('query running =================================== :')
        query = """UPDATE account_move SET state = 'posted'
            FROM account_journal
            where account_journal.id=account_move.journal_id 
            AND account_move.move_type='entry' 
            AND account_journal.type = 'cash' 
            AND account_move.date<'01/07/2019' 
            AND account_move.write_uid=2
            AND account_move.state='draft'"""
        self._cr.execute(query)
        self._cr.commit()

    @api.model
    def cron_jv_post_cash_try(self):
        _logger.info('query running =================================== :')
        try:
            query = """UPDATE account_move SET state = 'posted'
                FROM account_journal
                where account_journal.id=account_move.journal_id 
                AND account_move.move_type='entry' 
                AND account_journal.type = 'cash' 
                AND account_move.date<'01/07/2019' 
                AND account_move.write_uid=2
                AND account_move.state='draft'"""
            self._cr.execute(query)
            self._cr.commit()
        except Exception as e:
            _logger.info("---Exception raised : %r while sending OTP", e)

    @api.model
    def cron_jv_post_noncash(self):
        _logger.info('query running =================================== :')
        query = """UPDATE account_move SET state = 'posted'
            FROM account_journal
            where account_journal.id=account_move.journal_id 
            AND account_move.move_type='entry' 
            AND account_journal.type != 'cash' 
            AND account_move.date<'01/07/2019' 
            AND account_move.write_uid=2
            AND account_move.state='draft'"""
        self._cr.execute(query)
        self._cr.commit()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    schedule_id = fields.Many2one('sale.rent.schedule', 'Schedule')
    property_id = fields.Many2one('account.asset.asset',
                                  string='Property',
                                  help='Property Name.', tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset',
                                       string='Project',
                                       help='Property Name.', tracking=True)