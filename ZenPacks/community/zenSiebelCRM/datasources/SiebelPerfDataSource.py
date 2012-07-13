from Products.ZenModel.RRDDataSource import RRDDataSource
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence


class SiebelPerfDataSource(ZenPackPersistence, RRDDataSource):

    ZENPACKID = 'ZenPacks.community.zenSiebelCRM'

    SIEBEL = 'SiebelPerf'
    sourcetypes = (SIEBEL,)
    sourcetype = SIEBEL
    
    eventClass = '/Status/Siebel'
    component = "${here/CCalias}"
    server = "${dev/zSiebelServer}"
    #command = 'list statistics for component ${here/CCalias} show STAT_ALIAS,SD_DATATYPE,SD_SUBSYSTEM,CURR_VAL'
    command = 'list statistics for component ${here/CCalias} server ${dev/zSiebelServer} show STAT_ALIAS,CURR_VAL'

    _properties = RRDDataSource._properties + (
        {'id': 'command', 'type': 'string'},
        )

    def getDescription(self):
        return self.component

    def useZenCommand(self):
        return False


