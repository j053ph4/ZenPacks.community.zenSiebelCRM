from Products.ZenModel.OSComponent import OSComponent
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenRelations.RelSchema import *

'''
args:  classname,classname,properties,_properties,relname,sortkey,viewname
'''

class SiebelComponent(OSComponent, ManagedEntity, ZenPackPersistence):
    '''
    	basic Component class
    '''
    
    portal_type = meta_type = 'SiebelComponent'
    
    CCalias = None
    runState = None
    endTime = None
    CGalias = None
    startTime = None

    _properties = (
    {'id': 'CCalias', 'type': 'string','mode': '', 'switch': 'None' },
    {'id': 'runState', 'type': 'string','mode': '', 'switch': 'None' },
    {'id': 'endTime', 'type': 'string','mode': '', 'switch': 'None' },
    {'id': 'CGalias', 'type': 'string','mode': '', 'switch': 'None' },
    {'id': 'startTime', 'type': 'string','mode': '', 'switch': 'None' },

    )
    
    _relations = OSComponent._relations + (
        ('os', ToOne(ToManyCont, 'Products.ZenModel.OperatingSystem', 'siebelComponents')),
        )

    isUserCreatedFlag = True
    def isUserCreated(self):
        return self.isUserCreatedFlag
        
    def statusMap(self):
        self.status = 0
        return self.status
    
    def getStatus(self):
        return self.statusMap()
    
    def primarySortKey(self):
        return self.id
    
    def viewName(self):
        return self.id
    
    name = titleOrId = viewName


