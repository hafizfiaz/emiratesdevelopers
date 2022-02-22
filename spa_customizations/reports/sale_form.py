# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class report_sale_form(models.AbstractModel):
    _name = 'report.spa_customizations.report_sale_form_template'
    _description = 'Sale Form Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        so = self.env['sale.order'].browse(data['context'].get('active_ids'))
        rcpts = []
        if so:
            a = 0
            for line in so[0].receipt_ids:
                if line.state not in ['draft', 'proforma', 'cancelled', 'refused']:
                    rcpts.append(a)
                a += 1

        return {
            'doc_ids': data.get('ids', data['context'].get('active_ids')),
            'doc_model': 'sale.order',
            'docs': so,
            'rcpts': rcpts,
            'data': dict(
                data
            ),
        }


class report_golf_form_report(models.AbstractModel):
    _name = 'report.spa_customizations.report_golf_form_template'
    _description = 'Sale Form Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        so = self.env['sale.order'].browse(docids)
        rcpts = []
        if so:
            a = 0
            for line in so[0].receipt_ids:
                if line.state not in ['draft', 'proforma', 'cancelled', 'refused']:
                    rcpts.append(a)
                a += 1

        return {
            'doc_ids': data.get('ids', docids),
            'doc_model': 'sale.order',
            'docs': so,
            'rcpts': rcpts,
            'data': dict(
                data
            ),
        }