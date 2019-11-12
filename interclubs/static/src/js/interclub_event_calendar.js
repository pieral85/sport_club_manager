odoo.define('interclub_event.base_calendar', function (require) {
"use strict";

var BasicModel = require('web.BasicModel');


BasicModel.include({
    /** Overrides behavior of parent method which did not
    consider record's model. Default model is 'calendar.event'.
    However, by doing a delegation inheritance of this model,
    the record should be linked to the delegated model.
     */
    _fetchSpecialAttendeeStatus: function (record, fieldName) {
        var context = record.getContext({fieldName: fieldName});
        var attendeeIDs = record.data[fieldName] ? this.localData[record.data[fieldName]].res_ids : [];
        var meetingID = _.isNumber(record.res_id) ? record.res_id : false;
        return this._rpc({
            model: 'res.partner',
            method: 'get_attendee_detail_multi_model',
            args: [attendeeIDs, meetingID, record.model],
            context: context,
        }).then(function (result) {
            return _.map(result, function (d) {
                return _.object(['id', 'display_name', 'status', 'color'], d);
            });
        });
    },
});

});
