
(function() {
        
            function getPageContext() {
                return Zenoss.env.device_uid || Zenoss.env.PARENT_CONTEXT;
            }
        
            Ext.ComponentMgr.onAvailable('component-add-menu', function(config) {
                var menuButton = Ext.getCmp('component-add-menu');
                menuButton.menuItems.push({
                    xtype: 'menuitem',
                    text: _t('Add Siebel Component') + '...',
                    hidden: Zenoss.Security.doesNotHavePermission('Manage Device'),
                    handler: function() {
                        var win = new Zenoss.dialog.CloseDialog({
                            width: 300,
                            title: _t('Add Siebel Component'),
                            items: [{
                                xtype: 'form',
                                buttonAlign: 'left',
                                monitorValid: true,
                                labelAlign: 'top',
                                footerStyle: 'padding-left: 0',
                                border: false,
                                items:                         [
                            {
                                fieldLabel: 'CC Name', 
                                allowBlank: 'false', 
                                name: 'cc_name', 
                                width: 260, 
                                id: 'cc_nameField', 
                                xtype: 'textfield'
                            }, 
                            {
                                fieldLabel: 'CC Run Mode', 
                                allowBlank: 'false', 
                                name: 'cc_runmode', 
                                width: 260, 
                                id: 'cc_runmodeField', 
                                xtype: 'textfield'
                            }, 
                            {
                                fieldLabel: 'CG Alias', 
                                allowBlank: 'false', 
                                name: 'cg_alias', 
                                width: 260, 
                                id: 'cg_aliasField', 
                                xtype: 'textfield'
                            }, 
                            {
                                fieldLabel: 'CP Start Mode', 
                                allowBlank: 'false', 
                                name: 'cp_startmode', 
                                width: 260, 
                                id: 'cp_startmodeField', 
                                xtype: 'textfield'
                            }, 
                            {
                                fieldLabel: 'CT Alias', 
                                allowBlank: 'false', 
                                name: 'ct_alias', 
                                width: 260, 
                                id: 'ct_aliasField', 
                                xtype: 'textfield'
                            }, 
                            {
                                fieldLabel: 'Server', 
                                allowBlank: 'false', 
                                name: 'sv_name', 
                                width: 260, 
                                id: 'sv_nameField', 
                                xtype: 'textfield'
                            }
                        ]

                                ,
                                buttons: [{
                                    xtype: 'DialogButton',
                                    id: 'zenSiebelCRM-submit',
                                    text: _t('Add'),
                                    formBind: true,
                                    handler: function(b) {
                                        var form = b.ownerCt.ownerCt.getForm();
                                        var opts = form.getFieldValues();
                                        Zenoss.remote.zenSiebelCRMRouter.addSiebelComponentRouter(opts,
                                        function(response) {
                                            if (response.success) {
                                                new Zenoss.dialog.SimpleMessageDialog({
                                                    title: _t('Siebel Component Added'),
                                                    message: response.msg,
                                                    buttons: [{
                                                        xtype: 'DialogButton',
                                                        text: _t('OK'),
                                                        handler: function() { 
                                                            window.top.location.reload();
                                                            }
                                                        }]
                                                }).show();
                                            }
                                            else {
                                                new Zenoss.dialog.SimpleMessageDialog({
                                                    message: response.msg,
                                                    buttons: [{
                                                        xtype: 'DialogButton',
                                                        text: _t('OK'),
                                                        handler: function() { 
                                                            window.top.location.reload();
                                                            }
                                                        }]
                                                }).show();
                                            }
                                        });
                                    }
                                }, Zenoss.dialog.CANCEL]
                            }]
                        });
                        win.show();
                    }
                });
            });
        }()
);

