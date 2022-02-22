# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class CashflowReport(models.AbstractModel):
    _name = 'report.pdc_movement.pdc_bounced_movement_report'

    def get_result(self, start_date, end_date):
        data = {}
        data['cheques bounced'] = []
        data['cheques regular'] = []
        data['cheques security'] = []
        data['cheques rental'] = []
        data['cheques eoi'] = []
        data['cheques cleared'] = []
        bounced_cheques = self.env['account.payment'].search(['|',('collection_type_id.name','not in',['Rental Receipts','Security Cheques']),('collection_type_id','=',False), ('bounced_date','<',start_date),('state','=','refused'),('payment_type','=','inbound'),('chk','=',True)])
        bounced_cheques_date = self.env['account.payment'].search([('rd1_deposit_date','>=',start_date),('rd1_deposit_date','<=',end_date),('payment_type','=','inbound'),
                                                              ('re_deposit','>',0),('chk','=',True),('state','=','posted')])
        total_collected = 0.0
        data['bounced cheques view'] = []
        for line in bounced_cheques:
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

            data['bounced cheques view'].append(cheques_regular_view)
            total_collected += line.amount
        total_posted = 0.0
        for line in bounced_cheques_date:
            data['collected cheques view'] = []
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
        data['cheques bounced'].append(len(bounced_cheques)+len(bounced_cheques_date))
        data['cheques bounced'].append(total_collected+total_posted)
        cheques_regular = self.env['account.payment'].search([('bounced_date','>=',start_date),('bounced_date','<=',end_date),
                                                              ('state','in',['refused']),('payment_type','=','inbound'),
                                                              ('collection_type_id.name','not in',['Rental Receipts','Expression of Interest Collection','Security Cheques']),
                                                              ('chk','=',True)])
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

        cheques_eoi = self.env['account.payment'].search([('bounced_date','>=',start_date),('bounced_date','<=',end_date),
                                                              ('state','in',['refused']),('chk','=',True),('payment_type','=','inbound'),
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

        cheques_cleared = self.env['account.payment'].search([('rd1_deposit_date','>=',start_date),('rd1_deposit_date','<=',end_date),('payment_type','=','inbound'),
                                                              ('re_deposit','>',0),('chk','=',True),('state','=','posted')])
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

        return data


