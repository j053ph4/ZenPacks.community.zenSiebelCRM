
(function(){
    var ZC = Ext.ns('Zenoss.component');

    function render_link(ob) {
        if (ob && ob.uid) {
            return Zenoss.render.link(ob.uid);
        } else {
            return ob;
        }
    }
    
    function pass_link(ob){ 
        return ob; 
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
                        "sortable": "true", 
                        "width": 120, 
                        "header": "CC Name", 
                        "renderer": "pass_link", 
                        "id": "cc_name", 
                        "dataIndex": "cc_name"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "CC Run Mode", 
                        "renderer": "pass_link", 
                        "id": "cc_runmode", 
                        "dataIndex": "cc_runmode"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "CG Alias", 
                        "renderer": "pass_link", 
                        "id": "cg_alias", 
                        "dataIndex": "cg_alias"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "CP Start Mode", 
                        "renderer": "pass_link", 
                        "id": "cp_startmode", 
                        "dataIndex": "cp_startmode"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "CT Alias", 
                        "renderer": "pass_link", 
                        "id": "ct_alias", 
                        "dataIndex": "ct_alias"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "Run State", 
                        "renderer": "pass_link", 
                        "id": "getSiebelRunState", 
                        "dataIndex": "getSiebelRunState"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "Service", 
                        "renderer": "pass_link", 
                        "id": "getWinserviceLink", 
                        "dataIndex": "getWinserviceLink"
                    }, 
                    {
                        "sortable": "true", 
                        "width": 120, 
                        "header": "Server", 
                        "renderer": "pass_link", 
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

