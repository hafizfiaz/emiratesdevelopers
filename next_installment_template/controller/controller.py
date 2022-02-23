# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class ApproveRejectBooking(http.Controller):

    def booking_approve_function(self, booking_id):
        booking = request.env['sale.order'].sudo(2).search([('id','=',booking_id)])
        if booking:
            if booking.state == 'under_discount_approval':
                booking.action_discount_approved()
                return {
                    'name': 'Discount for Booking # '+ str(booking.booking_number) + ' is "Approved"',
                }
            else:
                return {
                    'name': 'Discount is already updated',
                }

    def booking_reject_function(self, booking_id):
        booking = request.env['sale.order'].sudo(2).search([('id','=',booking_id)])
        if booking:
            if booking.state == 'under_discount_approval':
                booking.action_is_buy_reject()
                return {
                    'name': 'Discount for Booking # '+ str(booking.booking_number) + ' is "Rejected"',
                }
            else:
                return {
                    'name': 'Discount is already updated',
                }


    @http.route(['/approve_booking'], type='http', auth="public", website=True)
    def schedule_approve(self, **kwargs):
        booking_id = int(kwargs.get('id'))
        return request.env['ir.ui.view']._render_template("next_installment_template.booking_approved",
                                  self.booking_approve_function(booking_id))

    @http.route(['/reject_booking'], type='http', auth="public", website=True)
    def schedule_reject(self, **kwargs):
        booking_id = int(kwargs.get('id'))
        return request.env['ir.ui.view']._render_template("next_installment_template.booking_rejected",
                                  self.booking_reject_function(booking_id))
