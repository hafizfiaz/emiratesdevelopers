# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
from odoo.tools.translate import _
import time
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo import http


class AccountAccount(models.Model):
    _inherit = "account.payment"

    visible_on_broker_statement = fields.Boolean('Visible on Broker Statement', default=True)
