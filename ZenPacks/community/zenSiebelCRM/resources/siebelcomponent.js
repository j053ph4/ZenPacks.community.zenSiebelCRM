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
                        fields: [
            {name: 'uid'},
            {name: 'severity'},
            {name: 'status'},
            {name: 'name'},{name: 'CCalias'},
                {name: 'runState'},
                {name: 'endTime'},
                {name: 'CGalias'},
                {name: 'startTime'},
                
            {name: 'usesMonitorAttribute'},
            {name: 'monitor'},
            {name: 'monitored'},
            {name: 'locking'},
            ]
        ,
                        columns:[{
            id: 'severity',
            dataIndex: 'severity',
            header: _t('Events'),
            renderer: Zenoss.render.severity,
            sortable: true,
            width: 50
        },{
            id: 'name',
            dataIndex: 'name',
            header: _t('Name'),
            sortable: true,
            width: 70
        },{
                    id: 'CCalias',
                    dataIndex: 'CCalias',
                    header: _t('CC Alias'),
                    sortable: true,
                    width: 133
                },{
                    id: 'runState',
                    dataIndex: 'runState',
                    header: _t('State'),
                    sortable: true,
                    width: 133
                },{
                    id: 'endTime',
                    dataIndex: 'endTime',
                    header: _t('End Time'),
                    sortable: true,
                    width: 133
                },{
                    id: 'CGalias',
                    dataIndex: 'CGalias',
                    header: _t('CG Alias'),
                    sortable: true,
                    width: 133
                },{
                    id: 'startTime',
                    dataIndex: 'startTime',
                    header: _t('Start Time'),
                    sortable: true,
                    width: 133
                },{
            id: 'monitored',
            dataIndex: 'monitored',
            header: _t('Monitored'),
            sortable: true,
            width: 65
        },{
            id: 'locking',
            dataIndex: 'locking',
            header: _t('Locking'),
            renderer: Zenoss.render.locking_icons,
            sortable: true,
            width: 65
        }]
                    });
                    ZC.SiebelComponentPanel.superclass.constructor.call(this, config);
                }
            });
            
            Ext.reg('SiebelComponentPanel', ZC.SiebelComponentPanel);
            ZC.registerName('SiebelComponent', _t('Siebel Component'), _t('Siebel Components'));
            
            })(); 

