######################################################################
#
# SiebelComponent modeler plugin
#
######################################################################
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.CollectorPlugin import CollectorPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap
from ZenPacks.community.zenSiebelCRM.SiebelHandler import SiebelHandler
from Products.ZenUtils.Utils import zenPath,prepId

class siebelComponentMap(PythonPlugin):
    """Map srvrmgmr output table to model."""

    relname = "siebelComponents"
    modname = "ZenPacks.community.zenSiebelCRM.SiebelComponent"
    
    deviceProperties = PythonPlugin.deviceProperties + (
                    'zSiebelGateway',
                    'zSiebelEnterprise',
                    'zSiebelServer',
                    'zSiebelUser',
                    'zSiebelPassword',
                    )
    
    def collect(self, device, log):
        self.siebel = SiebelHandler()
        self.siebel.initialize(device.zSiebelGateway,device.zSiebelEnterprise,device.zSiebelServer,device.zSiebelUser,device.zSiebelPassword,120,False)
        components = {}
        #command = 'list component show CC_ALIAS,CG_ALIAS,CP_DISP_RUN_STATE,CP_START_TIME,CP_END_TIME'
        command = 'list component show CC_ALIAS,CG_ALIAS,CP_DISP_RUN_STATE'
        if self.siebel.isServerRunning() == True:
            components = self.siebel.getCommandOutput(command)
            #log.debug('output: %s',components)
        self.siebel.terminate()
        
        return components
 
    def process(self, device, results, log):
        log.info('finding plugin %s for device %s', self.name(), device.id)
        rm = self.relMap()
        entries = len(results[results.keys()[0]])
        #log.debug("found %d components",entries)
        for e in range(entries):
            info = {}
            name = results['CC_ALIAS'][e]
            log.debug("found component: %s",name)
            if name != 'SiebSrvr':
                info['id'] = prepId(name)
                info['CGalias'] = results['CG_ALIAS'][e]
                info['CCalias'] = results['CC_ALIAS'][e]
                info['runState'] = results['CP_DISP_RUN_STATE'][e]
                #info['startTime'] = results['CP_START_TIME'][e]
                #info['endTime'] = results['CP_END_TIME'][e]
                om = self.objectMap(info)
                rm.append(om)
        return rm
