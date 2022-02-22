odoo.custom_approvals = function(instance, local) {
    var instance = odoo;
    var FormView = instance.web.FormView;

    // override load_record
//        Users.call('has_group', ['custom_approvals.contract_edit_rights']).done(function(is_employee) {
//            if (!is_employee) {
                FormView.include({
                    load_record: function(record) {
                    var res = this._super(record);
                    // disable only for cancel and paid account.invoice
                    if (record){
                        debugger;
                        if (this.model == 'approval.approval' && _.contains(['under_manager_review'], record.state) && (record.manager_ids.indexOf(213) !== -1)){
                                debugger;
                                $('button.oe_form_button.oe_highlight').show()
                            }else {
                                debugger;
                                $('button.oe_form_button.oe_highligh').hide()
                            }
                    }
                    // call super
                    return res;
                    }
                });
//            }
//        });
}

