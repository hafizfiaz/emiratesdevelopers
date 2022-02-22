# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    project = fields.Boolean('Project', default=False, tracking=True)