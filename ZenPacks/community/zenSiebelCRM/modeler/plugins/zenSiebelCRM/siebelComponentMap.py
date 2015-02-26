######################################################################
#
# SiebelComponent modeler plugin
#
######################################################################
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap
from ZenPacks.community.zenSiebelCRM.Definition import *
from ZenPacks.community.zenSiebelCRM.lib.SiebelHandler import SiebelHandler
from Products.ZenUtils.Utils import zenPath,prepId

__doc__ = """siebelComponentMap

siebelComponentMap detects Siebel CRM software components
This version adds a relation to associated winservices.

"""

                   
KEYMAP = {
          'CP_DISP_RUN_STATE': 'cp_disp_run_state',
          'CP_STARTMODE': 'cp_startmode',
          'CC_RUNMODE': 'cc_runmode',
          'CP_MAX_TASKS': 'cp_max_tasks',
          'CC_NAME': 'cc_name',
          'CC_ALIAS': 'cc_alias',
          'CG_ALIAS': 'cg_alias',
          'CT_ALIAS': 'ct_alias',
          'SV_NAME' : 'sv_name',
          }

class siebelComponentMap(PythonPlugin):
    """Map srvrmgmr output table to model."""
    constr = Construct(SiebelDefinition)
    
    compname = "os"
    relname = constr.relname
    modname = constr.zenpackComponentModule
    baseid = constr.baseid
    
    deviceProperties = PythonPlugin.deviceProperties + tuple([p[0] for p in SiebelDefinition.packZProperties])

    def startGtwySession(self, device, log):
        ''' connect to Siebel Server'''
        self.siebel = SiebelHandler()
        self.siebel.initialize(device.zSiebelGateway,device.zSiebelEnterprise,None,device.zSiebelUser,device.zSiebelPassword,120,True)

    def findServerName(self, device, log):
        '''find server name variable'''
        command = 'list servers show SBLSRVR_NAME,HOST_NAME'
        output = self.siebel.getCommandOutput(command)
        for o in output:
            #log.debug("finding server in :%s" % o)
            servername = o['SBLSRVR_NAME']
            hostname = o['HOST_NAME']
            if hostname.lower() in device.id.lower():  return servername
        return device.id
    
    def collect(self, device, log):
        log.info("collecting %s for %s." % (self.name(), device.id))
        self.startGtwySession(device, log)
        servername = self.findServerName(device, log)
        keys = ",".join(KEYMAP.keys())
        command = 'list component for server %s show %s' % (servername,keys)
        results = []
        output = self.siebel.getCommandOutput(command)
        for o in output:
            data = dict.fromkeys(KEYMAP.values())
            for k, v in o.items():
                data[KEYMAP[k]] = v
            data['gateway'] = device.zSiebelGateway
            data['enterprise'] = device.zSiebelEnterprise
            results.append(data)
        self.siebel.terminate()
        return results
    
    def process(self, device, results, log):
        log.info("The plugin %s returned %s results." % (self.name(), len(results)))
        rm = self.relMap()
        for result in results:
            name = result['cc_alias']
            if name == 'SiebSrvr': continue
            result.pop('cp_disp_run_state')
            om = self.objectMap(result)
            om.id = prepId(name)
            om.setWinservice = om.sv_name
            rm.append(om)
            #log.info(om)
        return rm

