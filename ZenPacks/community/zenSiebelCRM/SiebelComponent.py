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

    # Defining the "perfConf" action here causes the "Graphs" display to be
    # available for components of this type.
    # Defining the "perfConf" action here causes the "Graphs" display to be
    # available for components of this type.
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
        if self.runState == 'Online':
            self.status = 0
        elif self.runState == 'Running':
            self.status = 0
        elif self.runState == 'Unavailable':
            self.status = 1
        elif self.runState == 'Stopped':
            self.status = 2
        else:
            self.status = -1
        return self.status
            
    def getStatus(self):
        return self.statusMap()
        
        
    # Custom components must always implement the device method. The method
    # should return the device object that contains the component.
    def device(self):
        return self.siebelDevice()
    
    def monitored(self):
        if self.runState == 'Online':
            return True
        elif self.runState == 'Running':
            return True
        elif self.runState == 'Unavailable':
            return False
        elif self.runState == 'Stopped':
            return False
        else:
            return False
    
    
