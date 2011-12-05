from Products.ZenModel.RRDDataSource import RRDDataSource
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence


class SiebelTasksDataSource(ZenPackPersistence, RRDDataSource):

    ZENPACKID = 'ZenPacks.community.zenSiebelCRM'

    SIEBEL = 'SiebelTasks'
    sourcetypes = (SIEBEL,)
    sourcetype = SIEBEL
    
    # Set default values for properties inherited from RRDDataSource.
    eventClass = '/Status/Siebel'
    component = "${here/CCalias}"

    command = 'list tasks for component '+component+' show SV_NAME, CC_ALIAS, TK_PID, TK_DISP_RUNSTATE'

    _properties = RRDDataSource._properties + (
        {'id': 'command', 'type': 'string'},
        )

    def getDescription(self):
        return self.component

    def useZenCommand(self):
        return False

