# -*- coding: utf-8 -*-

from odoo import api, models


class ReportOverdueCollectionsRevised(models.AbstractModel):
    _name = 'report.revised_overdue_collection_report.odcr_revised'

    def get_recon_amount(self, iv, pay_jv_line):
        amount = 0
        inv_jv_line = iv.move_id.line_ids.filtered(lambda r: r.account_id.internal_type in ['receivable'])
        for jv_line in iv.payment_move_line_ids:
            if jv_line.matched_debit_ids and jv_line.id == pay_jv_line.id:
                for mdids in jv_line.matched_debit_ids:
                    if mdids.debit_move_id.id == inv_jv_line.id:
                        amount += mdids.amount
        # print(amount)
        return amount

    def get_result(self, start_date, end_date):
        projects = self.env['account.asset.asset'].search([('project', '=', True)])

        pw_result = {}
        uw_result = {}
        rsw_result = {}
        breakup_period = []
        breakup_before_paid = []
        breakup_fully_paid_before = []
        breakup_fully_paid_current = []
        inv_breakup = []
        realized_current_breakup = {}
        realized_pdc_breakup = {}
        unmatured_pdc_breakup = {}
        collection_unit_performance = {'Sale_Team': {'realize':0,'unmature':0,'total':0},
                                       'Receivable': {'realize':0,'unmature':0,'total':0}}
        invoices = self.env['account.move'].search([])
        properties = {}
        receivable_statuses = {}
        journals = []
        pdc_journals = []
        umn_journals = []
        collection_types = []
        pdc_collection_types = []
        unm_collection_types = []

        pdc_ids = self.env['account.payment'].search(
            [('payment_type', '=', 'inbound'), ('state', 'in', ['collected', 'deposited']),
             ('asset_project_id', '!=', False), '|', ('collection_type_id.name', '!=', 'Rental Receipts'),
             ('collection_type_id', '=', False)])
        from datetime import datetime, date
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        for pdc in pdc_ids:
            if pdc.date >= start_date and pdc.date <= end_date:
                if pdc.journal_id.name not in umn_journals:
                    unmatured_pdc_breakup[pdc.journal_id.name] = {}
                    umn_journals.append(pdc.journal_id.name)
                if pdc.collection_type_id.name not in unm_collection_types:
                    unm_collection_types.append(pdc.collection_type_id.name)
                if pdc.collection_type_id:
                    unmatured_pdc_breakup[pdc.journal_id.name][pdc.collection_type_id.name] = 0
                else:
                    unmatured_pdc_breakup[pdc.journal_id.name]['undefined'] = 0

        realized_ids = self.env['account.payment'].search(
            [('payment_type', '=', 'inbound'), ('state', '=', 'posted'),
                ('asset_project_id', '!=', False), '|', ('collection_type_id.name', '!=', 'Rental Receipts'),
                ('collection_type_id', '=', False)])
        for r1 in realized_ids:
            if r1.date >= start_date and r1.date <= end_date:
                if r1.journal_id.name not in journals:
                    realized_current_breakup[r1.journal_id.name] = {}
                    journals.append(r1.journal_id.name)
                if r1.collection_type_id.name not in collection_types:
                    collection_types.append(r1.collection_type_id.name)
                if r1.collection_type_id:
                    realized_current_breakup[r1.journal_id.name][r1.collection_type_id.name] = 0
                else:
                    realized_current_breakup[r1.journal_id.name]['undefined'] = 0
            if r1.chk:
                if r1.date < start_date and r1.paid_date:
                    if r1.paid_date.date() >= start_date and r1.paid_date.date() <= end_date:
                        if r1.journal_id.name not in pdc_journals:
                            realized_pdc_breakup[r1.journal_id.name] = {}
                            pdc_journals.append(r1.journal_id.name)
                        if r1.collection_type_id.name not in pdc_collection_types:
                            pdc_collection_types.append(r1.collection_type_id.name)
                        if r1.collection_type_id:
                            realized_pdc_breakup[r1.journal_id.name][r1.collection_type_id.name] = 0
                        else:
                            realized_pdc_breakup[r1.journal_id.name]['undefined'] = 0

        for project in projects:
            properties[project.name] = []
            receivable_statuses[project.name] = []
            pw_result[project.name] = {'name': project.name, 'due_total': 0, 'due_recon_before': 0,
                                       'due_recon_current': 0,'due_total_bls': 0, 'op_penalty': 0, 'current_due_total': 0,
                                       'current_due_recon_before': 0,'current_due_recon_current': 0,
                                       'current_due_total_bls': 0,'current_penalty': 0, 'closing_overdue_bls': 0, 'recon_op_overdue': 0,
                                       'recon_current_install': 0, 'recon_future_install': 0, 'recon_oqood': 0, 'recon_admin': 0, 'recon_other': 0,
                                       'unreconciled': 0, 'total_realized': 0, 'pdc_ope_against_overdue': 0,
                                       'pdc_against_current': 0, 'pdc_against_future': 0, 'pdc_not_defined': 0,
                                       'pdc_unmatured': 0, 'total_coll':0
                                       }
            due_recon_current = 0
            due_recon_before = 0
            current_due_total = 0
            current_due_recon_before = 0
            current_due_recon_current = 0
            current_due_recon_future = 0
            due_total = 0
            op_penalty = 0
            current_penalty = 0
            for inv in invoices.filtered(
                    lambda r: r.schedule_id and r.schedule_id.state == 'confirm' and r.state in ['open', 'paid'] and
                              r.asset_project_id.id == project.id):
                if inv.schedule_id.start_date <= end_date:
                    if inv.payment_move_line_ids:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                                         'recon': 0,'date': '', 'payment_no': '',
                                         'inv_no': '','inv_date': '','instal_due': ''}
                                check['inv_id'] = inv.id
                                check['id'] = payment.id
                                check['total'] = inv.amount_total
                                check['pay_total'] = payment.amount
                                check['recon'] = recon_amt
                                check['date'] = str(payment.date)
                                check['payment_no'] = str(payment.name)
                                check['inv_no'] = str(inv.number)
                                check['inv_date'] = str(inv.date_invoice)
                                check['instal_due'] = str(inv.installment_due_date)
                                inv_breakup.append(check)

                if inv.schedule_id.start_date >= start_date and inv.schedule_id.start_date <= end_date:
                    current_due_total += inv.amount_total
                    if inv.schedule_id.penalty:
                        current_penalty += inv.schedule_id.penalty
                    if inv.payment_move_line_ids:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    current_due_recon_current += recon_amt
                                if payment.date < start_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    current_due_recon_before += recon_amt
                if inv.schedule_id.start_date < start_date:
                    due_total += inv.amount_total
                    if inv.schedule_id.penalty:
                        op_penalty += inv.schedule_id.penalty
                    if inv.payment_move_line_ids:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    due_recon_current += recon_amt
                                if payment.date < start_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    due_recon_before += recon_amt
                if inv.schedule_id.start_date > end_date:
                    for pay in inv.payment_move_line_ids:
                        if pay.payment_id:
                            payment = pay.payment_id
                            pay_jv_line = payment.move_entry_ids.filtered(
                                lambda r: r.account_id.internal_type in ['receivable'])
                            if payment.date >= start_date and payment.date <= end_date:
                                recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                current_due_recon_future += recon_amt

            pw_result[project.name]['op_penalty'] = op_penalty
            pw_result[project.name]['current_penalty'] = current_penalty
            pw_result[project.name]['due_total'] = due_total
            pw_result[project.name]['due_recon_before'] = due_recon_before
            pw_result[project.name]['due_recon_current'] = due_recon_current
            due_total_bls = due_total - due_recon_before - due_recon_current
            pw_result[project.name]['due_total_bls'] = due_total_bls

            pw_result[project.name]['current_due_total'] = current_due_total
            pw_result[project.name]['current_due_recon_before'] = current_due_recon_before
            pw_result[project.name]['current_due_recon_current'] = current_due_recon_current
            current_due_total_bls = current_due_total - current_due_recon_before - current_due_recon_current
            pw_result[project.name]['current_due_total_bls'] = current_due_total_bls


            pw_result[project.name]['closing_overdue_bls'] = current_due_total_bls + due_total_bls
            pw_result[project.name]['recon_op_overdue'] = due_recon_current
            pw_result[project.name]['recon_current_install'] = current_due_recon_current
            pw_result[project.name]['recon_future_install'] = current_due_recon_future

            invs = self.env['account.move'].search([('asset_project_id','=',project.id),('state','in',['open','paid'])])
            oqood_amount = 0
            admin_amount = 0
            for iv in invs:
                oqood = False
                admin = False
                for line in iv.invoice_line_ids:
                    if 'oqood' in line.account_id.name.lower():
                        oqood = True
                    if 'admin' in line.account_id.name.lower():
                        admin = True
                if oqood:
                    for pay in iv.payment_move_line_ids:
                        if pay.payment_id:
                            payment = pay.payment_id
                            pay_jv_line = payment.move_entry_ids.filtered(lambda r: r.account_id.internal_type in ['receivable'])
                            if payment.date >= start_date and payment.date <= end_date:
                                oqood_amount += self.get_recon_amount(iv,pay_jv_line)
                if admin:
                    for pay in iv.payment_move_line_ids:
                        if pay.payment_id:
                            payment = pay.payment_id
                            pay_jv_line = payment.move_entry_ids.filtered(lambda r: r.account_id.internal_type in ['receivable'])
                            if payment.date >= start_date and payment.date <= end_date:
                                admin_amount += self.get_recon_amount(iv,pay_jv_line)

            pw_result[project.name]['recon_oqood'] = oqood_amount
            pw_result[project.name]['recon_admin'] = admin_amount

            total_unreconciled_amount = 0
            total_realized_pdc = 0
            total_realized_all = 0
            realized_ids = project.env['account.payment'].search(
                [('payment_type', '=', 'inbound'), ('state', '=','posted'),
                 ('asset_project_id', '=', project.id),'|',('collection_type_id.name','!=','Rental Receipts'),
                 ('collection_type_id','=',False)])
            # for r1 in realized_ids:
            #     if r1.date >= start_date and r1.date <= end_date:
            #         if r1.journal_id.name not in journals:
            #             realized_current_breakup[r1.journal_id.name] = {}
            #             journals.append(r1.journal_id.name)
            #         if r1.collection_type_id.name not in collection_types:
            #             collection_types.append(r1.collection_type_id.name)
            #         if r1.collection_type_id:
            #             realized_current_breakup[r1.journal_id.name][r1.collection_type_id.name] = 0
            #         else:
            #             realized_current_breakup[r1.journal_id.name]['undefined'] = 0
            #     if r1.chk:
            #         if r1.date < start_date and r1.paid_date:
            #             if r1.journal_id.name not in pdc_journals:
            #                 realized_pdc_breakup[r1.journal_id.name] = {}
            #                 pdc_journals.append(r1.journal_id.name)
            #             if r1.collection_type_id.name not in pdc_collection_types:
            #                 pdc_collection_types.append(r1.collection_type_id.name)
            #             if r1.collection_type_id:
            #                 realized_pdc_breakup[r1.journal_id.name][r1.collection_type_id.name] = 0
            #             else:
            #                 realized_pdc_breakup[r1.journal_id.name]['undefined'] = 0
            # print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
            # print(realized_current_breakup)
            # print(realized_pdc_breakup)
            # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")


            for realize in realized_ids:
                pay_jv_line = realize.move_entry_ids.filtered(
                    lambda r: r.account_id.internal_type in ['receivable'])
                if realize.date >= start_date and realize.date <= end_date:
                    if realize.collection_type_id:
                        realized_current_breakup[realize.journal_id.name][realize.collection_type_id.name] += realize.amount
                    else:
                        realized_current_breakup[realize.journal_id.name]['undefined'] += realize.amount

                    if realize.collection_type_id.name == 'Sale Collection - Sale Team Unit':
                        collection_unit_performance['Sale_Team']['realize'] += realize.amount
                        collection_unit_performance['Sale_Team']['total'] += realize.amount
                    if realize.collection_type_id.name == 'Sale Collection - Receivable Collection Unit':
                        collection_unit_performance['Receivable']['realize'] += realize.amount
                        collection_unit_performance['Receivable']['total'] += realize.amount

                    total_unreconciled_amount += realize.unreconciled_amount
                    total_realized_all += realize.amount
                    # if realize.invoice_ids or realize.reconciled_invoice_ids:
                    #     if realize.invoice_ids:
                    #         for inv in realize.invoice_ids:
                    #             recon_amt = self.get_recon_amount(inv, pay_jv_line)
                    #             current_due_recon_before += recon_amt
                    #             check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                    #                      'recon': 0,'date': '', 'payment_no': '',
                    #                      'inv_no': '','inv_date': '','instal_due': ''}
                    #             check['inv_id'] = inv.id
                    #             check['id'] = realize.id
                    #             check['total'] = inv.amount_total
                    #             check['pay_total'] = realize.amount
                    #             check['recon'] = recon_amt
                    #             check['date'] = str(realize.date)
                    #             check['payment_no'] = str(realize.name)
                    #             check['inv_no'] = str(inv.number)
                    #             check['inv_date'] = str(inv.date_invoice)
                    #             check['instal_due'] = str(inv.installment_due_date)
                    #             breakup_period.append(check)
                    #     else:
                    #         for inv in realize.invoice_ids:
                    #             recon_amt = self.get_recon_amount(inv, pay_jv_line)
                    #             current_due_recon_before += recon_amt
                    #             check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                    #                      'recon': 0,'date': '', 'payment_no': '',
                    #                      'inv_no': '','inv_date': '','instal_due': ''}
                    #             check['inv_id'] = inv.id
                    #             check['id'] = realize.id
                    #             check['total'] = inv.amount_total
                    #             check['pay_total'] = realize.amount
                    #             check['recon'] = recon_amt
                    #             check['date'] = str(realize.date)
                    #             check['payment_no'] = str(realize.name)
                    #             check['inv_no'] = str(inv.number)
                    #             check['inv_date'] = str(inv.date_invoice)
                    #             check['instal_due'] = str(inv.installment_due_date)
                    #             breakup_period.append(check)
                if realize.chk:
                    if realize.date < start_date and realize.paid_date:
                        if realize.paid_date.date() >= start_date and realize.paid_date.date() <= end_date:
                            if realize.collection_type_id:
                                realized_pdc_breakup[realize.journal_id.name][
                                    realize.collection_type_id.name] += realize.amount
                            else:
                                realized_pdc_breakup[realize.journal_id.name]['undefined'] += realize.amount
                            total_realized_pdc += realize.amount
                            # if realize.invoice_ids or realize.reconciled_invoice_ids:
                            #     if realize.invoice_ids:
                            #         for inv in realize.invoice_ids:
                            #             recon_amt = self.get_recon_amount(inv, pay_jv_line)
                            #             current_due_recon_before += recon_amt
                            #             check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                            #                      'recon': 0, 'date': '', 'payment_no': '',
                            #                      'inv_no': '', 'inv_date': '', 'instal_due': ''}
                            #             check['inv_id'] = inv.id
                            #             check['id'] = realize.id
                            #             check['total'] = inv.amount_total
                            #             check['pay_total'] = realize.amount
                            #             check['recon'] = recon_amt
                            #             check['date'] = str(realize.date)
                            #             check['payment_no'] = str(realize.name)
                            #             check['inv_no'] = str(inv.number)
                            #             check['inv_date'] = str(inv.date_invoice)
                            #             check['instal_due'] = str(inv.installment_due_date)
                            #             breakup_before_paid.append(check)
                            #     else:
                            #         for inv in realize.invoice_ids:
                            #             recon_amt = self.get_recon_amount(inv, pay_jv_line)
                            #             current_due_recon_before += recon_amt
                            #             check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                            #                      'recon': 0, 'date': '', 'payment_no': '',
                            #                      'inv_no': '', 'inv_date': '', 'instal_due': ''}
                            #             check['inv_id'] = inv.id
                            #             check['id'] = realize.id
                            #             check['total'] = inv.amount_total
                            #             check['pay_total'] = realize.amount
                            #             check['recon'] = recon_amt
                            #             check['date'] = str(realize.date)
                            #             check['payment_no'] = str(realize.name)
                            #             check['inv_no'] = str(inv.number)
                            #             check['inv_date'] = str(inv.date_invoice)
                            #             check['instal_due'] = str(inv.installment_due_date)
                            #             breakup_before_paid.append(check)
            total_realized = total_realized_all + total_realized_pdc

            pw_result[project.name]['unreconciled'] = total_unreconciled_amount
            pw_result[project.name]['total_realized'] = total_realized

            pdc_against_op = 0
            pdc_against_curr = 0
            pdc_against_future = 0
            pdc_total_unmat = 0
            pdc_undefined = 0
            pdc_ids = project.env['account.payment'].search(
                [('payment_type', '=', 'inbound'), ('state', 'in', ['collected', 'deposited']),
                 ('asset_project_id', '=', project.id),'|',('collection_type_id.name','!=','Rental Receipts'),
                 ('collection_type_id','=',False)])
            for pdc in pdc_ids:
                if pdc.date >= start_date and pdc.date <= end_date:
                    if pdc.collection_type_id:
                        unmatured_pdc_breakup[pdc.journal_id.name][pdc.collection_type_id.name] += pdc.amount
                    else:
                        unmatured_pdc_breakup[pdc.journal_id.name]['undefined'] += pdc.amount
                    if pdc.collection_type_id.name == 'Sale Collection - Sale Team Unit':
                        collection_unit_performance['Sale_Team']['unmature'] += pdc.amount
                        collection_unit_performance['Sale_Team']['total'] += pdc.amount
                    if pdc.collection_type_id.name == 'Sale Collection - Receivable Collection Unit':
                        collection_unit_performance['Receivable']['unmature'] += pdc.amount
                        collection_unit_performance['Receivable']['total'] += pdc.amount
                    # if pdc.related_installment_ids:
                    #     for ri in pdc.related_installment_ids:
                    #         if ri.start_date < start_date:
                    #             pdc_against_op += pdc.amount
                    #             pdc_total_unmat += pdc.amount
                    #         if ri.start_date >= start_date and ri.start_date <= end_date:
                    #             pdc_against_curr += pdc.amount
                    #             pdc_total_unmat += pdc.amount
                    #         if ri.start_date > end_date:
                    #             pdc_against_future += pdc.amount
                    #             pdc_total_unmat += pdc.amount
                    # else:
                    #     pdc_undefined += pdc.amount
                    #     pdc_total_unmat += pdc.amount

            pw_result[project.name]['pdc_ope_against_overdue'] = pdc_against_op
            pw_result[project.name]['pdc_against_current'] = pdc_against_curr
            pw_result[project.name]['pdc_against_future'] = pdc_against_future
            pw_result[project.name]['pdc_not_defined'] = pdc_undefined
            pw_result[project.name]['pdc_unmatured'] = pdc_total_unmat

            pw_result[project.name]['total_coll'] = total_realized + pdc_total_unmat


            units = self.env['account.asset.asset'].search([('parent_id', '=', project.id)])
            uw_result[project.name] = {}
            for unit in units:
                properties[project.name].append(unit.name)
                uw_result[project.name][unit.name] = {'name': unit.name, 'due_total': 0, 'due_recon_before': 0,
                                           'due_recon_current': 0, 'due_total_bls': 0, 'op_penalty': 0, 'current_due_total': 0,
                                           'current_due_recon_before': 0, 'current_due_recon_current': 0,
                                           'current_due_total_bls': 0, 'current_penalty': 0, 'closing_overdue_bls': 0, 'recon_op_overdue': 0,
                                           'recon_current_install': 0,'recon_future_install': 0, 'recon_oqood': 0, 'recon_admin': 0,
                                           'recon_other': 0,
                                           'unreconciled': 0, 'total_realized': 0, 'pdc_ope_against_overdue': 0,
                                           'pdc_against_current': 0, 'pdc_against_future': 0, 'pdc_not_defined': 0,
                                           'pdc_unmatured': 0, 'total_coll': 0
                                           }
                due_recon_current = 0
                due_recon_before = 0
                current_due_total = 0
                current_due_recon_before = 0
                current_due_recon_current = 0
                current_due_recon_future = 0
                due_total = 0
                op_penalty = 0
                current_penalty = 0
                for inv in invoices.filtered(
                        lambda r: r.schedule_id and r.schedule_id.state == 'confirm' and r.state in ['open', 'paid'] and
                                  r.asset_project_id.id == project.id and r.property_id.id == unit.id):
                    if inv.schedule_id.start_date >= start_date and inv.schedule_id.start_date <= end_date:
                        current_due_total += inv.amount_total
                        if inv.schedule_id.penalty:
                            current_penalty += inv.schedule_id.penalty
                        if inv.payment_move_line_ids:
                            for pay in inv.payment_move_line_ids:
                                if pay.payment_id:
                                    payment = pay.payment_id
                                    pay_jv_line = payment.move_entry_ids.filtered(
                                        lambda r: r.account_id.internal_type in ['receivable'])
                                    if payment.date >= start_date and payment.date <= end_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        current_due_recon_current += recon_amt
                                    if payment.date < start_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        current_due_recon_before += recon_amt
                    if inv.schedule_id.start_date < start_date:
                        due_total += inv.amount_total
                        if inv.schedule_id.penalty:
                            op_penalty += inv.schedule_id.penalty
                        if inv.payment_move_line_ids:
                            for pay in inv.payment_move_line_ids:
                                if pay.payment_id:
                                    payment = pay.payment_id
                                    pay_jv_line = payment.move_entry_ids.filtered(
                                        lambda r: r.account_id.internal_type in ['receivable'])
                                    if payment.date >= start_date and payment.date <= end_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        due_recon_current += recon_amt
                                    if payment.date < start_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        due_recon_before += recon_amt
                    if inv.schedule_id.start_date > end_date:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    current_due_recon_future += recon_amt

                uw_result[project.name][unit.name]['op_penalty'] = op_penalty
                uw_result[project.name][unit.name]['current_penalty'] = current_penalty
                uw_result[project.name][unit.name]['due_total'] = due_total
                uw_result[project.name][unit.name]['due_recon_before'] = due_recon_before
                uw_result[project.name][unit.name]['due_recon_current'] = due_recon_current
                due_total_bls = due_total - due_recon_before - due_recon_current
                uw_result[project.name][unit.name]['due_total_bls'] = due_total_bls

                uw_result[project.name][unit.name]['current_due_total'] = current_due_total
                uw_result[project.name][unit.name]['current_due_recon_before'] = current_due_recon_before
                uw_result[project.name][unit.name]['current_due_recon_current'] = current_due_recon_current
                current_due_total_bls = current_due_total - current_due_recon_before - current_due_recon_current
                uw_result[project.name][unit.name]['current_due_total_bls'] = current_due_total_bls

                uw_result[project.name][unit.name]['closing_overdue_bls'] = current_due_total_bls + due_total_bls
                uw_result[project.name][unit.name]['recon_op_overdue'] = due_recon_current
                uw_result[project.name][unit.name]['recon_current_install'] = current_due_recon_current
                uw_result[project.name][unit.name]['recon_future_install'] = current_due_recon_future

                invs = self.env['account.move'].search(
                    [('asset_project_id', '=', project.id),('property_id', '=', unit.id), ('state', 'in', ['open', 'paid'])])
                oqood_amount = 0
                admin_amount = 0
                for iv in invs:
                    oqood = False
                    admin = False
                    for line in iv.invoice_line_ids:
                        if 'oqood' in line.account_id.name.lower():
                            oqood = True
                        if 'admin' in line.account_id.name.lower():
                            admin = True
                    if oqood:
                        for pay in iv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    oqood_amount += self.get_recon_amount(iv, pay_jv_line)
                    if admin:
                        for pay in iv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    admin_amount += self.get_recon_amount(iv, pay_jv_line)

                uw_result[project.name][unit.name]['recon_oqood'] = oqood_amount
                uw_result[project.name][unit.name]['recon_admin'] = admin_amount

                total_unreconciled_amount = 0
                total_realized_pdc = 0
                total_realized_all = 0
                realized_ids = project.env['account.payment'].search(
                    [('payment_type', '=', 'inbound'), ('state', '=', 'posted'),
                     ('asset_project_id', '=', project.id),('property_id', '=', unit.id),'|',
                     ('collection_type_id.name','!=','Rental Receipts'),('collection_type_id','=',False)])
                for realize in realized_ids:
                    pay_jv_line = realize.move_entry_ids.filtered(
                        lambda r: r.account_id.internal_type in ['receivable'])
                    if realize.date >= start_date and realize.date <= end_date:
                        total_unreconciled_amount += realize.unreconciled_amount
                        total_realized_all += realize.amount
                    if realize.chk:
                        if realize.date < start_date and realize.paid_date:
                            if realize.paid_date.date() >= start_date and realize.paid_date.date() <= end_date:
                                total_realized_pdc += realize.amount
                total_realized = total_realized_all + total_realized_pdc

                uw_result[project.name][unit.name]['unreconciled'] = total_unreconciled_amount
                uw_result[project.name][unit.name]['total_realized'] = total_realized

                pdc_against_op = 0
                pdc_against_curr = 0
                pdc_against_future = 0
                pdc_total_unmat = 0
                pdc_undefined = 0
                pdc_ids = project.env['account.payment'].search(
                    [('payment_type', '=', 'inbound'), ('state', 'in', ['collected', 'deposited']),
                     ('asset_project_id', '=', project.id),('property_id', '=', unit.id),'|',
                     ('collection_type_id.name','!=','Rental Receipts'),('collection_type_id','=',False)])
                # for pdc in pdc_ids:
                #     if pdc.date >= start_date and pdc.date <= end_date:
                #         if pdc.related_installment_ids:
                #             for ri in pdc.related_installment_ids:
                #                 if ri.start_date < start_date:
                #                     pdc_against_op += pdc.amount
                #                     pdc_total_unmat += pdc.amount
                #                 if ri.start_date >= start_date and ri.start_date <= end_date:
                #                     pdc_against_curr += pdc.amount
                #                     pdc_total_unmat += pdc.amount
                #                 if ri.start_date > end_date:
                #                     pdc_against_future += pdc.amount
                #                     pdc_total_unmat += pdc.amount
                #         else:
                #             pdc_undefined += pdc.amount
                #             pdc_total_unmat += pdc.amount

                uw_result[project.name][unit.name]['pdc_ope_against_overdue'] = pdc_against_op
                uw_result[project.name][unit.name]['pdc_against_current'] = pdc_against_curr
                uw_result[project.name][unit.name]['pdc_against_future'] = pdc_against_future
                uw_result[project.name][unit.name]['pdc_not_defined'] = pdc_undefined
                uw_result[project.name][unit.name]['pdc_unmatured'] = pdc_total_unmat

                uw_result[project.name][unit.name]['total_coll'] = total_realized + pdc_total_unmat


            receivabless = self.env['receivable.status'].search([('active', '=', True)])
            rsw_result[project.name] = {}
            for sts in receivabless:
                receivable_statuses[project.name].append(sts.name)
                rsw_result[project.name][sts.name] = {'name': sts.name, 'due_total': 0, 'due_recon_before': 0,
                                           'due_recon_current': 0, 'due_total_bls': 0, 'current_due_total': 0,
                                           'current_due_recon_before': 0, 'current_due_recon_current': 0,
                                           'current_due_total_bls': 0, 'closing_overdue_bls': 0
                                           }
                due_recon_current = 0
                due_recon_before = 0
                current_due_total = 0
                current_due_recon_before = 0
                current_due_recon_current = 0
                current_due_recon_future = 0
                due_total = 0
                for inv in invoices.filtered(
                        lambda r: r.schedule_id and r.schedule_id.state == 'confirm' and r.state in ['open', 'paid'] and
                                  r.asset_project_id.id == project.id and r.schedule_id.receivable_status_id.id == sts.id):
                    if inv.schedule_id.start_date >= start_date and inv.schedule_id.start_date <= end_date:
                        current_due_total += inv.amount_total
                        if inv.payment_move_line_ids:
                            for pay in inv.payment_move_line_ids:
                                if pay.payment_id:
                                    payment = pay.payment_id
                                    pay_jv_line = payment.move_entry_ids.filtered(
                                        lambda r: r.account_id.internal_type in ['receivable'])
                                    if payment.date >= start_date and payment.date <= end_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        current_due_recon_current += recon_amt
                                    if payment.date < start_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        current_due_recon_before += recon_amt
                    if inv.schedule_id.start_date < start_date:
                        due_total += inv.amount_total
                        if inv.payment_move_line_ids:
                            for pay in inv.payment_move_line_ids:
                                if pay.payment_id:
                                    payment = pay.payment_id
                                    pay_jv_line = payment.move_entry_ids.filtered(
                                        lambda r: r.account_id.internal_type in ['receivable'])
                                    if payment.date >= start_date and payment.date <= end_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        due_recon_current += recon_amt
                                        check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                                                 'recon': 0, 'date': '', 'payment_no': '',
                                                 'inv_no': '', 'inv_date': '', 'instal_due': '', 'rstatus': ''}
                                        check['inv_id'] = inv.id
                                        check['id'] = payment.id
                                        check['total'] = inv.amount_total
                                        check['pay_total'] = payment.amount
                                        check['recon'] = recon_amt
                                        check['date'] = str(payment.date)
                                        check['payment_no'] = str(payment.name)
                                        check['inv_no'] = str(inv.number)
                                        check['inv_date'] = str(inv.date_invoice)
                                        check['instal_due'] = str(inv.installment_due_date)
                                        check['rstatus'] = str(inv.schedule_id.receivable_status_id.name)
                                        breakup_fully_paid_current.append(check)
                                    if payment.date < start_date:
                                        recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                        due_recon_before += recon_amt
                                        check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                                                 'recon': 0, 'date': '', 'payment_no': '',
                                                 'inv_no': '', 'inv_date': '', 'instal_due': '', 'rstatus': ''}
                                        check['inv_id'] = inv.id
                                        check['id'] = payment.id
                                        check['total'] = inv.amount_total
                                        check['pay_total'] = payment.amount
                                        check['recon'] = recon_amt
                                        check['date'] = str(payment.date)
                                        check['payment_no'] = str(payment.name)
                                        check['inv_no'] = str(inv.number)
                                        check['inv_date'] = str(inv.date_invoice)
                                        check['instal_due'] = str(inv.installment_due_date)
                                        check['rstatus'] = str(inv.schedule_id.receivable_status_id.name)
                                        breakup_fully_paid_before.append(check)
                    if inv.schedule_id.start_date > end_date:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    current_due_recon_future += recon_amt

                rsw_result[project.name][sts.name]['due_total'] = due_total
                rsw_result[project.name][sts.name]['due_recon_before'] = due_recon_before
                rsw_result[project.name][sts.name]['due_recon_current'] = due_recon_current
                due_total_bls = due_total - due_recon_before - due_recon_current
                rsw_result[project.name][sts.name]['due_total_bls'] = due_total_bls

                rsw_result[project.name][sts.name]['current_due_total'] = current_due_total
                rsw_result[project.name][sts.name]['current_due_recon_before'] = current_due_recon_before
                rsw_result[project.name][sts.name]['current_due_recon_current'] = current_due_recon_current
                current_due_total_bls = current_due_total - current_due_recon_before - current_due_recon_current
                rsw_result[project.name][sts.name]['current_due_total_bls'] = current_due_total_bls

                rsw_result[project.name][sts.name]['closing_overdue_bls'] = current_due_total_bls + due_total_bls

            rsw_result[project.name]['undefined'] = {'name': 'undefined', 'due_total': 0, 'due_recon_before': 0,
                                                  'due_recon_current': 0, 'due_total_bls': 0, 'current_due_total': 0,
                                                  'current_due_recon_before': 0, 'current_due_recon_current': 0,
                                                  'current_due_total_bls': 0, 'closing_overdue_bls': 0
                                                  }
            due_recon_current = 0
            due_recon_before = 0
            current_due_total = 0
            current_due_recon_before = 0
            current_due_recon_current = 0
            current_due_recon_future = 0
            due_total = 0
            for inv in invoices.filtered(
                    lambda r: r.schedule_id and r.schedule_id.state == 'confirm' and r.state in ['open', 'paid'] and
                              r.asset_project_id.id == project.id and r.schedule_id.receivable_status_id.id == False):
                if inv.schedule_id.start_date >= start_date and inv.schedule_id.start_date <= end_date:
                    current_due_total += inv.amount_total
                    if inv.payment_move_line_ids:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    current_due_recon_current += recon_amt
                                if payment.date < start_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    current_due_recon_before += recon_amt
                if inv.schedule_id.start_date < start_date:
                    due_total += inv.amount_total
                    if inv.payment_move_line_ids:
                        for pay in inv.payment_move_line_ids:
                            if pay.payment_id:
                                payment = pay.payment_id
                                pay_jv_line = payment.move_entry_ids.filtered(
                                    lambda r: r.account_id.internal_type in ['receivable'])
                                if payment.date >= start_date and payment.date <= end_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    due_recon_current += recon_amt
                                    check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                                             'recon': 0, 'date': '', 'payment_no': '',
                                             'inv_no': '', 'inv_date': '', 'instal_due': '', 'rstatus': ''}
                                    check['inv_id'] = inv.id
                                    check['id'] = payment.id
                                    check['total'] = inv.amount_total
                                    check['pay_total'] = payment.amount
                                    check['recon'] = recon_amt
                                    check['date'] = str(payment.date)
                                    check['payment_no'] = str(payment.name)
                                    check['inv_no'] = str(inv.number)
                                    check['inv_date'] = str(inv.date_invoice)
                                    check['instal_due'] = str(inv.installment_due_date)
                                    check['rstatus'] = str(inv.schedule_id.receivable_status_id.name)
                                    breakup_fully_paid_current.append(check)
                                if payment.date < start_date:
                                    recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                    due_recon_before += recon_amt
                                    check = {'name': project.name, 'id': 0, 'inv_id': 0, 'pay_total': 0, 'total': 0,
                                             'recon': 0, 'date': '', 'payment_no': '',
                                             'inv_no': '', 'inv_date': '', 'instal_due': '', 'rstatus': ''}
                                    check['inv_id'] = inv.id
                                    check['id'] = payment.id
                                    check['total'] = inv.amount_total
                                    check['pay_total'] = payment.amount
                                    check['recon'] = recon_amt
                                    check['date'] = str(payment.date)
                                    check['payment_no'] = str(payment.name)
                                    check['inv_no'] = str(inv.number)
                                    check['inv_date'] = str(inv.date_invoice)
                                    check['instal_due'] = str(inv.installment_due_date)
                                    check['rstatus'] = str(inv.schedule_id.receivable_status_id.name)
                                    breakup_fully_paid_before.append(check)
                if inv.schedule_id.start_date > end_date:
                    for pay in inv.payment_move_line_ids:
                        if pay.payment_id:
                            payment = pay.payment_id
                            pay_jv_line = payment.move_entry_ids.filtered(
                                lambda r: r.account_id.internal_type in ['receivable'])
                            if payment.date >= start_date and payment.date <= end_date:
                                recon_amt = self.get_recon_amount(inv, pay_jv_line)
                                current_due_recon_future += recon_amt

            rsw_result[project.name]['undefined']['due_total'] = due_total
            rsw_result[project.name]['undefined']['due_recon_before'] = due_recon_before
            rsw_result[project.name]['undefined']['due_recon_current'] = due_recon_current
            due_total_bls = due_total - due_recon_before - due_recon_current
            rsw_result[project.name]['undefined']['due_total_bls'] = due_total_bls

            rsw_result[project.name]['undefined']['current_due_total'] = current_due_total
            rsw_result[project.name]['undefined']['current_due_recon_before'] = current_due_recon_before
            rsw_result[project.name]['undefined']['current_due_recon_current'] = current_due_recon_current
            current_due_total_bls = current_due_total - current_due_recon_before - current_due_recon_current
            rsw_result[project.name]['undefined']['current_due_total_bls'] = current_due_total_bls

            rsw_result[project.name]['undefined']['closing_overdue_bls'] = current_due_total_bls + due_total_bls


        print("--------------------realized_current_breakup---------------------------")
        print(realized_current_breakup)
        print("--------------------realized_pdc_breakup-------------------------------")
        print(realized_pdc_breakup)
        return projects, pw_result, properties, uw_result, breakup_before_paid, breakup_period, inv_breakup,  journals,\
               collection_types, realized_current_breakup, pdc_journals, pdc_collection_types, realized_pdc_breakup,\
               umn_journals, unm_collection_types, unmatured_pdc_breakup, collection_unit_performance, \
               receivable_statuses, rsw_result, breakup_fully_paid_current, breakup_fully_paid_before


