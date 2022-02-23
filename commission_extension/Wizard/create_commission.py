# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class CreateCommissionWiz(models.TransientModel):
    _name = "create.commission.wiz"
    _description = 'Create Commission Wiz'

    @api.depends('booking_id')
    def _get_comm_details(self):
        for res in self:
            is_com1 = False
            is_com2 = False
            is_com3 = False
            is_agent_com = False
            comm_obj = res.env['commission.invoice'].search([('related_booking_id', '=', res.booking_id.id),('state', '!=', 'cancel')])
            if comm_obj:
                for rec in comm_obj:
                    for team_agent in res.team_up_agents:
                        if rec.agent.id == team_agent.id:
                            is_com1 = True
                    if rec.agent.id == res.agent_id.id:
                        is_agent_com = True
                    if rec.agent.id == res.agent.id:
                        is_com1 = True
                    if rec.agent.id == res.agent2.id:
                        is_com2 = True
                    if rec.agent.id == res.agent3.id:
                        is_com3 = True
            res.is_com1 = is_com1
            res.is_com2 = is_com2
            res.is_com3 = is_com3
            res.is_agent_com = is_agent_com

    booking_id = fields.Many2one('sale.order', 'Booking')
    agent_ref = fields.Boolean(string='Agent Ref.', related='booking_id.agent_ref')
    agent_id = fields.Many2one('res.partner', string='Agent Name', related='booking_id.agent_id')
    agent_commission_type_id = fields.Many2one('commission.type', string='Agent Commission', related='booking_id.agent_commission_type_id')
    commission_type_id = fields.Many2one('commission.type', string='Type', related='booking_id.commission_type_id')
    agent = fields.Many2one('res.partner',  string='Agent', related='booking_id.agent')
    commission = fields.Boolean('Commission', related='booking_id.commission')
    total_commission = fields.Float(string="Total Commission", related='booking_id.total_commission')

    team_up = fields.Boolean('Team Up', related='booking_id.team_up')
    commission_share_perc = fields.Float('Commission Share (%)', related='booking_id.commission_share_perc')
    commission_share_amount = fields.Float(string='Commission Share Amount', related='booking_id.commission_share_amount')
    team_up_agents = fields.Many2many('res.users', string='Team Up Agents', related='booking_id.team_up_agents')

    commission_type_id2 = fields.Many2one('commission.type', string='Type', related='booking_id.commission_type_id2')
    agent2 = fields.Many2one('res.partner',  string='Agent', related='booking_id.agent2')
    commission2 = fields.Boolean('2nd Commission', related='booking_id.commission2')
    total_commission2 = fields.Float(string="Total Commission", related='booking_id.total_commission2')

    commission_type_id3 = fields.Many2one('commission.type', string='Type', related='booking_id.commission_type_id3')
    agent3 = fields.Many2one('res.partner', string='Agent', related='booking_id.agent3')
    commission3 = fields.Boolean('3rd Commission', related='booking_id.commission3')
    total_commission3 = fields.Float(string="Total Commission", related='booking_id.total_commission3')

    is_agent_com = fields.Boolean('is agent comm', compute='_get_comm_details')
    is_com1 = fields.Boolean('is comm1', compute='_get_comm_details')
    is_com2 = fields.Boolean('is comm2', compute='_get_comm_details')
    is_com3 = fields.Boolean('is comm3', compute='_get_comm_details')

    def create_commission(self):
        for data in self:
            booking = data.booking_id
            if booking.commission and not booking.team_up and not data.is_com1:
                if booking.total_commission == 0.00:
                    raise Warning(
                        _('Total Commission must be grater than zero.'))
                line_vlas = {
                    'name': 'Commission',
                    'commission_type': 'fixed',
                    'rent_amt': booking.price,
                    'amount': booking.total_commission,
                }
                vals = {
                    'commission_for_sale': True,
                    'partner_id': booking.partner_id.id,
                    'related_booking_id': booking.id,
                    'property_id': booking.property_id.id,
                    'asset_project_id': booking.asset_project_id.id,
                    'commission_type_id': booking.commission_type_id.id,
                    'agent': booking.agent.id,
                    'booking_date': booking.booking_date,
                    'total_price': booking.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas)],
                }

                booking.env['commission.invoice'].create(vals)
                booking.write({'commission_create': True})

            if booking.commission and booking.team_up and not data.is_com1:
                if booking.commission_share_amount == 0.00:
                    raise Warning(
                        _('Total Share Commission must be grater than zero.'))
                line_vlas = {
                    'name': 'Commission',
                    'commission_type': 'fixed',
                    'rent_amt': booking.price,
                    'amount': booking.commission_share_amount,
                }
                vals = {
                    'commission_for_sale': True,
                    'partner_id': booking.partner_id.id,
                    'related_booking_id': booking.id,
                    'property_id': booking.property_id.id,
                    'asset_project_id': booking.asset_project_id.id,
                    'commission_type_id': booking.commission_type_id.id,
                    'agent': booking.agent.id,
                    'booking_date': booking.booking_date,
                    'total_price': booking.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas)],
                }
                self.env['commission.invoice'].create(vals)
                for su in booking.team_up_agents:
                    line_vlas = {
                        'name': 'Commission',
                        'commission_type': 'fixed',
                        'rent_amt': booking.price,
                        'amount': booking.commission_share_amount,
                    }
                    vals = {
                        'commission_for_sale': True,
                        'partner_id': booking.partner_id.id,
                        'related_booking_id': booking.id,
                        'property_id': booking.property_id.id,
                        'asset_project_id': booking.asset_project_id.id,
                        'commission_type_id': booking.commission_type_id.id,
                        'agent': su.partner_id.id,
                        'booking_date': booking.booking_date,
                        'total_price': booking.price,
                        'description': "1.	SPA is signed & in all sense correct.\n"
                                       "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                       "3.	Oqood has been received.\n"
                                       "4.	Admin has been received.\n"
                                       "5.	PDCs have been received (where applicable).\n",
                        'commission_line': [(0, 0, line_vlas)],
                    }

                    booking.env['commission.invoice'].create(vals)
                booking.write({'commission_create': True})

            if booking.agent_ref and not data.is_agent_com:
                if booking.net_commission_sp == 0.00:
                    raise Warning(
                        _('Total Commission2 must be grater than zero.'))
                line_vlas2 = {
                    'name': 'External Agent Commission',
                    'commission_type': 'fixed',
                    'rent_amt': booking.price,
                    'amount': booking.net_commission_sp,
                }
                vals2 = {
                    'commission_for_sale': True,
                    'partner_id': booking.partner_id.id,
                    'related_booking_id': booking.id,
                    'property_id': booking.property_id.id,
                    'agent_ref': booking.agent_ref,
                    'asset_project_id': booking.asset_project_id.id,
                    'commission_type_id': booking.agent_commission_type_id.id,
                    'agent': booking.agent_id.id,
                    'booking_date': booking.booking_date,
                    'total_price': booking.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas2)],
                }
                booking.env['commission.invoice'].create(vals2)
                booking.write({'commission_create': True})

            if booking.commission2  and not data.is_com2:
                if booking.total_commission2 == 0.00:
                    raise Warning(
                        _('Total Commission must be grater than zero.'))
                line_vlas4 = {
                    'name': 'Commission',
                    'commission_type': 'fixed',
                    'rent_amt': booking.price,
                    'amount': booking.total_commission2,
                }
                vals4 = {
                    'commission_for_sale': True,
                    'partner_id': booking.partner_id.id,
                    'related_booking_id': booking.id,
                    'property_id': booking.property_id.id,
                    'commission_type_id': booking.commission_type_id2.id,
                    'asset_project_id': booking.asset_project_id.id,
                    'agent': booking.agent2.id,
                    'booking_date': booking.booking_date,
                    'total_price': booking.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas4)],
                }
                booking.env['commission.invoice'].create(vals4)
                booking.write({'commission_create': True})

            if booking.commission3 and not data.is_com3:
                if booking.total_commission3 == 0.00:
                    raise Warning(
                        _('Total Commission must be grater than zero.'))
                line_vlas3 = {
                    'name': 'Commission3',
                    'commission_type': 'fixed',
                    'rent_amt': booking.price,
                    'amount': booking.total_commission3,
                }
                vals3 = {
                    'commission_for_sale': True,
                    'partner_id': booking.partner_id.id,
                    'related_booking_id': booking.id,
                    'property_id': booking.property_id.id,
                    'asset_project_id': booking.asset_project_id.id,
                    'commission_type_id': booking.commission_type_id3.id,
                    'agent': booking.agent3.id,
                    'booking_date': booking.booking_date,
                    'total_price': booking.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas3)],
                }
                booking.env['commission.invoice'].create(vals3)
                booking.write({'commission_create': True})
