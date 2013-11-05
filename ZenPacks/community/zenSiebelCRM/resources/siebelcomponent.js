
(function(){
    var ZC = Ext.ns('Zenoss.component');

    function render_link(ob) {
        if (ob && ob.uid) {
            return Zenoss.render.link(ob.uid);
        } else {
            return ob;
        }
    }

    ZC.SiebelComponentPanel = Ext.extend(ZC.ComponentGridPanel, {
        constructor: function(config) {
            config = Ext.applyIf(config||{}, {
                componentType: 'SiebelComponent',
                autoExpandColumn: 'name', 
                fields:                 [
                    {
                        "name": "uid"
                    }, 
                    {
                        "name": "severity"
                    }, 
                    {
                        "name": "status"
                    }, 
                    {
                        "name": "name"
                    }, 
                    {
                        "name": "cc_name"
                    }, 
                    {
                        "name": "cc_runmode"
                    }, 
                    {
                        "name": "cg_alias"
                    }, 
                    {
                        "name": "cp_startmode"
                    }, 
                    {
                        "name": "ct_alias"
                    }, 
                    {
                        "name": "getSiebelRunState"
                    }, 
                    {
                        "name": "getWinserviceLink"
                    }, 
                    {
                        "name": "sv_name"
                    }, 
                    {
                        "name": "usesMonitorAttribute"
                    }, 
                    {
                        "name": "monitor"
                    }, 
                    {
                        "name": "monitored"
                    }, 
                    {
                        "name": "locking"
                    }
                ]
,
                columns:                [
                    {
                        "sortable": "true", 
                        "width": 50, 
                        "header": "Events", 
                        "renderer": Zenoss.render.severity, 
                        "id": "severity", 
                        "dataIndex": "severity"
                    }, 
                    {
                        "header": "Name", 
                        "width": 70, 
                        "sortable": "true", 
                        "id": "name", 
                        "dataIndex": "name"
                    }, 
                    {
                        "header": "CC Name", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "cc_name", 
                        "dataIndex": "cc_name"
                    }, 
                    {
                        "header": "CC Run Mode", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "cc_runmode", 
                        "dataIndex": "cc_runmode"
                    }, 
                    {
                        "header": "CG Alias", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "cg_alias", 
                        "dataIndex": "cg_alias"
                    }, 
                    {
                        "header": "CP Start Mode", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "cp_startmode", 
                        "dataIndex": "cp_startmode"
                    }, 
                    {
                        "header": "CT Alias", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "ct_alias", 
                        "dataIndex": "ct_alias"
                    }, 
                    {
                        "header": "Run State", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "getSiebelRunState", 
                        "dataIndex": "getSiebelRunState"
                    }, 
                    {
                        "header": "Winservice", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "getWinserviceLink", 
                        "dataIndex": "getWinserviceLink"
                    }, 
                    {
                        "header": "Server", 
                        "width": 120, 
                        "sortable": "true", 
                        "id": "sv_name", 
                        "dataIndex": "sv_name"
                    }, 
                    {
                        "header": "Monitored", 
                        "width": 65, 
                        "sortable": "true", 
                        "id": "monitored", 
                        "dataIndex": "monitored"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 65, 
                        "header": "Locking", 
                        "renderer": Zenoss.render.locking_icons, 
                        "id": "locking", 
                        "dataIndex": "locking"
                    }
                ]

            });
            ZC.SiebelComponentPanel.superclass.constructor.call(this, config);
        }
    });
    
    Ext.reg('SiebelComponentPanel', ZC.SiebelComponentPanel);
    ZC.registerName('SiebelComponent', _t('Siebel Component'), _t('Siebel Components'));
    
    })();

