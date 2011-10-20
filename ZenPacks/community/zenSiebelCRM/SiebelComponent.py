from Products.ZenModel.DeviceComponent import DeviceComponent
from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenModel.ZenossSecurity import ZEN_CHANGE_DEVICE
from Products.ZenRelations.RelSchema import ToManyCont, ToOne


class SiebelComponent(DeviceComponent, ManagedEntity):
    """
    SiebelComponent is a Siebel CRM component
    """
    meta_type = portal_type = "SiebelComponent"

    CGalias = ''
    CCalias = ''
    runState = ''
    startTime = ''
    endTime = ''
    status = 1

    _properties = ManagedEntity._properties + (
        {'id': 'CGalias', 'type': 'string', 'mode': ''},
        {'id': 'CCalias', 'type': 'string', 'mode': ''},
        {'id': 'runState', 'type': 'string', 'mode': ''},
        {'id': 'startTime', 'type': 'string', 'mode': ''},
        {'id': 'endTime', 'type': 'string', 'mode': ''},
        {'id':'status', 'type':'int', 'mode':''},
    )

    _relations = ManagedEntity._relations + (
        ('siebelDevice', ToOne(ToManyCont,
            'ZenPacks.community.zenSiebelCRM.SiebelDevice.SiebelDevice',
            'siebelComponent',
            ),
        ),
    )

    factory_type_information = ({
        'actions': ({
            'id': 'perfConf',
            'name': 'Template',
            'action': 'objTemplates',
            'permissions': (ZEN_CHANGE_DEVICE,),
        },),
    },)
    
    def viewName(self):
        return self.CCalias
    
    titleOrId = name = viewName
    
    def primarySortKey(self):
        return self.CCalias
    
    def statusMap(self):
        """ map run state to zenoss status
        """
        stateValue = self.getStatusValue()
        if stateValue == -1:
            self.runState = 'Unknown'
            self.status = -1
        elif stateValue == 0:
            self.runState = 'Unavailable'
            self.status = 2
        elif stateValue == 1:
            self.runState = 'Stopped'
            self.status = 1
        elif stateValue == 2:
            self.runState = 'Online'
            self.status = 0
        elif stateValue == 3:
            self.runState = 'Running'
            self.status = 0
        return self.status
            
    def getStatus(self):
        return self.statusMap()

    def device(self):
        return self.siebelDevice()
    
    def monitored(self):
        return True
    
    def getStatusValue(self):
        """ return numerical value of status check [1|0]
        """
        return int(self.cacheRRDValue('get-stats_runState',0))
