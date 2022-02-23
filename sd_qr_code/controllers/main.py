# See LICENSE file for full copyright and licensing details

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from datetime import datetime
import werkzeug

from odoo.addons.payment_paypal.controllers.main import PaypalController

class QRPage(Home):

    def web_data(self, model, selected_id):
        records = []
        print("WEB_data")
        print(model)
        print(selected_id)
        table_header = []
        records_list = []
        heading = ''
        if model and selected_id:
            # selected_id = int(selected_id) - 56738
            if model =="booking":
                table_header = ['Project','Property','Customer Name','Booking #','Property Sale Price']
                heading = "Reservation Form"
                model = 'crm.booking'
                records = request.env[model].sudo().search(
                    [('id', '=', selected_id)])
                records_list.append(records[0].asset_project_id.name)
                records_list.append(records[0].property_id.name)
                records_list.append(records[0].partner_id.name)
                records_list.append(records[0].booking_number)
                records_list.append('{:,.2f}'.format(records[0].price))
            if model =="booking_closure":
                table_header = ['Customer Name','Project','Property','Unit Type','List Price',
                                'Discount','Selling Price','External Agent','Agent Commission %',
                                'Agent Commission Amount (AED)']
                heading = "Closure Form"
                model = 'crm.booking'
                records = request.env[model].sudo().search(
                    [('id', '=', selected_id)])
                records_list.append(records[0].partner_id.name)
                records_list.append(records[0].asset_project_id.name)
                records_list.append(records[0].property_id.name)
                records_list.append(records[0].unit_type_id.name)
                records_list.append('{:,.2f}'.format(records[0].property_price))
                records_list.append('{:,.2f}'.format(records[0].discount_value))
                records_list.append('{:,.2f}'.format(records[0].price))
                records_list.append(records[0].agent_id.name)
                records_list.append(records[0].net_commission_perc)
                records_list.append(records[0].net_commission_sp)
            if model =="sale":
                table_header = ['Project','Property','Customer Name','Booking #','Booking Status', 'Property Sale Price','Oqood Charged','Admin Fee Charged','Other Charges','Total SPA Value']
                heading = "SPA Form"
                model = 'sale.order'
                records = request.env[model].sudo().search(
                    [('id', '=', selected_id)])
                records_list.append(records[0].booking_id.asset_project_id.name)
                records_list.append(records[0].booking_id.property_id.name)
                records_list.append(records[0].partner_id.name)
                records_list.append(records[0].booking_id.booking_number)
                records_list.append(records[0].booking_id.is_buy_state)
                records_list.append(records[0].booking_id.price)
                records_list.append(records[0].oqood_fee)
                records_list.append(records[0].admin_fee)
                records_list.append(records[0].other_charges)
                records_list.append(records[0].total_spa_value)
            if model =="payment":
                table_header = ['Receipt #','Date','Customer Name','Project','Property','Receipt Amount','Payment Type']
                heading = "Receipts"
                model = 'account.payment'
                records = request.env[model].sudo().search(
                    [('id', '=', selected_id)])
                # records_list.append(records[0].booking_id.asset_project_id.name)
                # records_list.append(records[0].booking_id.property_id.name)
                records_list.append(records[0].name )
                records_list.append(records[0].date)
                records_list.append(records[0].partner_id.name)
                records_list.append(records[0].asset_project_id.name )
                records_list.append(records[0].property_id.name )
                records_list.append(records[0].amount)
                records_list.append(records[0].journal_id.name )
            if model =="multipayment":
                table_header = ['Date','Customer Name','Receipt Amount','Payment Type']
                heading = "Receipts"
                model = 'account.voucher.collection'
                records = request.env[model].sudo().search(
                    [('id', '=', selected_id)])
                # records_list.append(records[0].booking_id.asset_project_id.name)
                # records_list.append(records[0].booking_id.property_id.name)
                records_list.append(records[0].date)
                records_list.append(records[0].partner_id.name)
                records_list.append(records[0].amount_total)
                records_list.append(records[0].collection_line[0].journal_id.name)
        return {
            'heading': heading,
            'table_header': table_header,
            'records': records_list,
            'nabar': 'inv',
        }

    @http.route(['/developers'], type='http', auth="public", website=True)
    def developers_web(self, **kwargs):
        print("DEvelopers Page")
        print(kwargs)
        if kwargs.get('model') and kwargs.get('rec_id'):
            model = kwargs.get('model')
            selected_id = kwargs.get('rec_id')
        print (kwargs.get('model'))
        print (kwargs.get('rec_id'))
        return request.env['ir.ui.view']._render_template("sd_qr_code.web_view_onload",
                              self.web_data(kwargs.get('model'),kwargs.get('rec_id')))

