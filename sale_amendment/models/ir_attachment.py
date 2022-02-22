# -*- coding: utf-8 -*-
from openerp.osv import fields,osv


class document_file(osv.osv):
    _inherit = 'ir.attachment'


    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        requirement_obj = self.pool.get('mrp.production.workcenter.line')
        # HRN 20171103
        context = dict(context).copy()
        context.update({'from_doc': True})
        # HRN
        for attach in self.browse(cr, uid, ids, context=context):
            all_1_2 = True
            for requirement in attach.requirement_ids:
                for doc in requirement.attachments:
                    if doc.id != attach.id and doc.state not in ('draft'):
                        all_1_2 = False
                if all_1_2:
                    requirement_obj.action_draft(cr, uid, [requirement.id], context=context)
                else:
                    min_status = self.check_min_status(cr, uid, ids, attach.id, requirement.attachments)
                    if min_status == 'draft':
                        requirement_obj.action_draft(cr, uid, [requirement.id], context=context)
                    elif min_status == 'under_collection':
                        requirement_obj.action_under_collection(cr, uid, [requirement.id], context=context)
                    elif min_status == 'under_doc_officer_review':
                        requirement_obj.action_under_doc_officer_review(cr, uid, [requirement.id], context=context)
                    elif min_status == 'under_dispatch_officer_review':
                        requirement_obj.action_under_dispatch_officer_review(cr, uid, [requirement.id], context=context)
                    elif min_status == 'dispatched':
                        requirement_obj.action_dispatched(cr, uid, [requirement.id], context=context)
                    elif min_status == 'cancel':
                        requirement_obj.action_cancel(cr, uid, [requirement.id], context=context)
                    elif min_status == 'not_applicable':
                        requirement_obj.action_not_applicable(cr, uid, [requirement.id], context=context)
                    elif min_status == 'under_process':
                        requirement_obj.action_under_process(cr, uid, [requirement.id], context=context)

        return True