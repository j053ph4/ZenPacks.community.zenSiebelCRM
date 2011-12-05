from Products.ZenModel.RRDDataSource import RRDDataSource
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence


class SiebelStatusDataSource(ZenPackPersistence, RRDDataSource):

    # All subclasses of ZenPackPersistence need to set their ZENPACKID.
    ZENPACKID = 'ZenPacks.community.zenSiebelCRM'

    SIEBEL = 'SiebelStatus'
    sourcetypes = (SIEBEL,)
    sourcetype = SIEBEL
    
    # Set default values for properties inherited from RRDDataSource.
    eventClass = '/Status/Siebel'
    component = "${here/CCalias}"
    # Add default values for custom properties of this datasource.
    command = command = 'list component '+component+' show CC_ALIAS,CP_DISP_RUN_STATE,CP_START_TIME,CP_END_TIME'

    _properties = RRDDataSource._properties + (
        {'id': 'command', 'type': 'string'},
        )

    def getDescription(self):
        return self.component

    def useZenCommand(self):
        return False

