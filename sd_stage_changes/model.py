from odoo import api, fields, models, _


class ProjectStage(models.Model):
    _name = 'project.stage'
    _description = 'Task Stage'
    _order = 'sequence'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_ids = fields.Many2many('ir.model', string='Model')
    responsible_id = fields.Many2many('res.users', 'responsible_user_rel', 'responsible_id', 'user_id',
                                      string='Responsible Person')
    user_id = fields.Many2many("res.users", 'visible_user_rel', 'visible_id', 'user_id', string='Users')
    user_ids = fields.Many2many("res.users", 'visible_users_rel', 'visible_id', 'user_id', string='Visibility To Users',
                                compute='get_users_from_groups', store=True)
    group_ids = fields.Many2many("res.groups", 'visible_groups_rel', 'visible_id', 'groups_id',
                                 string='Visibility To Groups')
    legend_priority = fields.Char(
        string='Starred Explanation', translate=True,
        help='Explanation text to help users using the star on tasks or issues in this stage.')
    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda s: _('Blocked'), translate=True, required=True,
        help='Override the default value displayed for the blocked state for kanban selection, when the task or issue is in that stage.')
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda s: _('Ready for Next Stage'), translate=True, required=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')
    legend_normal = fields.Char(
        'Grey Kanban Label', default=lambda s: _('In Progress'), translate=True, required=True,
        help='Override the default value displayed for the normal state for kanban selection, when the task or issue is in that stage.')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'project.task')],
        help="If set an email will be sent to the customer when the task or issue reaches this step.")
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there are no records in that stage to display.')
    rating_template_id = fields.Many2one(
        'mail.template',
        string='Rating Email Template',
        help="If set and if the project's rating configuration is 'Rating when changing stage', then an email will be sent to the customer when the task reaches this step.")
    auto_validation_kanban_state = fields.Boolean('Automatic kanban status', default=False,
                                                  help="Automatically modify the kanban state when the customer replies to the feedback for this stage.\n"
                                                       " * A good feedback from the customer will update the kanban state to 'ready for the new stage' (green bullet).\n"
                                                       " * A medium or a bad feedback will set the kanban state to 'blocked' (red bullet).\n")

    @api.depends('group_ids', 'group_ids.users')
    def get_users_from_groups(self):
        for rec in self:
            users = []
            if rec.group_ids:
                for group in rec.group_ids:
                    for line in group.users:
                        users.append(line.id)
            rec.user_ids = users

    def get_partner_ids(self, user_ids):
        if user_ids:
            anb = str([user.partner_id.email for user in user_ids]).replace('[', '').replace(']', '')
            return anb.replace("'", '')
