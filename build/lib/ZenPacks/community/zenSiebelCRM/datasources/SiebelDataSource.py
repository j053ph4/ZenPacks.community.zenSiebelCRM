from Products.ZenModel.RRDDataSource import RRDDataSource
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence


class SiebelDataSource(ZenPackPersistence, RRDDataSource):

    ZENPACKID = 'ZenPacks.community.zenSiebelCRM'

    SIEBEL = 'Siebel'
    sourcetypes = (SIEBEL,)
    sourcetype = SIEBEL
    
    eventClass = '/Status/Siebel'
    component = "${here/CCalias}"
    command = ''

    _properties = RRDDataSource._properties + (
        {'id': 'command', 'type': 'string'},
        )

    def getDescription(self):
        return self.component

    def useZenCommand(self):
        return False


