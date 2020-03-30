odoo.define('club.s_active_roles_editor', function (require) {
'use strict';

var sOptions = require('web_editor.snippets.options');
var wUtils = require('website.utils');

sOptions.registry.js_get_committee_selectRole = sOptions.Class.extend({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _renderCustomXML: function (uiFragment) {
        return this._rpc({
            model: 'role',
            method: 'search_read',
            args: [wUtils.websiteDomain(this), ['name']],
        }).then(roles => {
            const menuEl = uiFragment.querySelector('[name="role_selection"]');
            for (const role of roles) {
                const el = document.createElement('we-button');
                el.dataset.selectDataAttribute = role.id;
                el.textContent = role.name;
                menuEl.appendChild(el);
            }
        });
    },
});
});
