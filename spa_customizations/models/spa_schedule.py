# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SPAScheduleView(models.TransientModel):
    _name = 'spa.schedule.view'
    _description = 'SPA Schedule View'

    schedule_a_eng = fields.Text('Schedule A Eng')
    schedule_b_eng = fields.Text('Schedule B Eng')
    schedule_c_eng = fields.Text('Schedule C Eng')
    schedule_d_eng = fields.Text('Schedule D Eng')
    schedule_e_eng = fields.Text('Schedule E Eng')
    schedule_f_eng = fields.Text('Schedule F Eng')
    schedule_g_eng = fields.Text('Schedule G Eng')
    schedule_h_eng = fields.Text('Schedule H Eng')
    schedule_i_eng = fields.Text('Schedule I Eng')
