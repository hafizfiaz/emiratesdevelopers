# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class CashflowReport(models.AbstractModel):
    _name = 'report.pdc_movement.pdc_movement_report'

    def get_result(self, start_date, end_date):
        data = {}
        data['collected cheques'] = []
        data['cheques regular'] = []
        data['cheques rental'] = []
        data['cheques eoi'] = []
        data['cheques deposited'] = []
        data['cheques cleared'] = []
        data['cheques stale'] = []
        data['cheques bounced'] = []
        data['closing balance cheques'] = []
        collected_cheques = self.env['account.payment'].search([('collection_type_id.name','not in',['Security Cheques']),('payment_type','=','inbound'),('date','<',start_date),('state','=','collected'),('chk','=',True)])
        posted_cheques = self.env['account.payment'].search([('collection_type_id.name','not in',['Security Cheques']),('payment_type','=','inbound'),('date','<',start_date),('paid_date','>=',start_date),('paid_date','<=',end_date),('chk','=',True)])
        total_collected = 0.0
        data['collected cheques view'] = []
        for line in collected_cheques:

            cheques_regular_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['collected cheques view'].append(cheques_regular_view)
            total_collected += line.amount
        total_posted = 0.0
        for line in posted_cheques:

            cheques_regular_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['collected cheques view'].append(cheques_regular_view)
            total_posted += line.amount
        data['collected cheques'].append(len(collected_cheques)+len(posted_cheques))
        data['collected cheques'].append(total_collected+total_posted)
        cheques_regular = self.env['account.payment'].search([('date','>=',start_date),('date','<=',end_date),
                                                              ('state','not in',['draft','cancelled']),('chk','=',True),('payment_type','=','inbound'),
                                                              ('collection_type_id.name','not in',['Rental Receipts','Expression of Interest Collection','Security Cheques'])])
        total = 0.0
        data['cheques regular view'] = []
        for line in cheques_regular:
            cheques_regular_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques regular view'].append(cheques_regular_view)
            total += line.amount
        data['cheques regular'].append(len(cheques_regular))
        data['cheques regular'].append(total)

        cheques_rental = self.env['account.payment'].search([('date','>=',start_date),('date','<=',end_date),
                                                              ('state','not in',['draft','cancelled']),('chk','=',True),('payment_type','=','inbound'),
                                                              ('collection_type_id.name','in',['Rental Receipts'])])
        total = 0.0
        data['cheques rental view'] = []
        for line in cheques_rental:
            cheques_security_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques rental view'].append(cheques_security_view)
            total += line.amount
        data['cheques rental'].append(len(cheques_rental))
        data['cheques rental'].append(total)

        cheques_eoi = self.env['account.payment'].search([('date','>=',start_date),('date','<=',end_date),
                                                              ('state','not in',['draft','cancelled']),('chk','=',True),('payment_type','=','inbound'),
                                                              ('collection_type_id.name','in',['Expression of Interest Collection'])])
        total = 0.0
        data['cheques eoi view'] = []
        for line in cheques_eoi:
            cheques_security_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques eoi view'].append(cheques_security_view)
            total += line.amount
        data['cheques eoi'].append(len(cheques_eoi))
        data['cheques eoi'].append(total)

        cheques_deposited = self.env['account.payment'].search([('collection_type_id.name','not in',['Security Cheques']),('posting_date','>=',start_date),('posting_date','<=',end_date),('payment_type','=','inbound'),
                                                              ('state','in',['deposited']),('chk','=',True)])
        total = 0.0
        data['cheques deposited view'] = []
        for line in cheques_deposited:
            cheques_security_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques deposited view'].append(cheques_security_view)
            total += line.amount
        data['cheques deposited'].append(len(cheques_deposited))
        data['cheques deposited'].append(total)

        cheques_cleared = self.env['account.payment'].search([('collection_type_id.name','not in',['Security Cheques']),('paid_date','>=',start_date),('paid_date','<=',end_date),('payment_type','=','inbound'),
                                                              ('state','in',['posted']),('chk','=',True)])
        total = 0.0
        data['cheques cleared view'] = []
        for line in cheques_cleared:
            cheques_security_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques cleared view'].append(cheques_security_view)
            total += line.amount
        data['cheques cleared'].append(len(cheques_cleared))
        data['cheques cleared'].append(total)

        cheques_stale = self.env['account.payment'].search([('collection_type_id.name','not in',['Security Cheques']),('date','<',start_date), ('state_update_date','>=',start_date),('state_update_date','<=',end_date),('payment_type','=','inbound'),
                                                              ('state','in',['settle','outsourced','replaced']),('chk','=',True)])
        total = 0.0
        data['cheques stale view'] = []
        for line in cheques_stale:
            cheques_security_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques stale view'].append(cheques_security_view)
            total += line.amount
        data['cheques stale'].append(len(cheques_stale))
        data['cheques stale'].append(total)

        cheques_bounced = self.env['account.payment'].search([('collection_type_id.name','not in',['Security Cheques']),('bounced_date','>=',start_date),('bounced_date','<=',end_date),('payment_type','=','inbound'),
                                                              ('state','in',['refused']),('chk','=',True)])
        total = 0.0
        data['cheques bounced view'] = []
        for line in cheques_bounced:
            cheques_security_view = {
                'create_date': line.create_date,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'write_date': line.write_date,
                'check_number': line.check_number,
                'maturity_date': line.maturity_date,
                'partner_name': line.partner_id.name,
                'asset_project_name': line.asset_project_id.name,
                'property_name': line.property_id.name,
                'collection_type_name': line.collection_type_id.name,
                'amount': line.amount,
                'bank_deposit': line.bank_deposit.bank_id.name,
                'reference': line.reference,
            }

            data['cheques bounced view'].append(cheques_security_view)
            total += line.amount
        data['cheques bounced'].append(len(cheques_bounced))
        data['cheques bounced'].append(total)

        return data


