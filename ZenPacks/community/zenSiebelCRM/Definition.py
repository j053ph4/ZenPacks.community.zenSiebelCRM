from ZenPacks.community.ConstructionKit.BasicDefinition import *
from ZenPacks.community.ConstructionKit.Construct import *


ROOT = "ZenPacks.community"
BASE = "zenSiebelCRM"
VERSION = Version(2, 8, 0)

siebelRunStateMap = {
               4: 'Running',
               3: 'Online',
               2: 'Unavailable',
               1: 'Stopped',
               0: 'Shutdown',
               -1: 'Unknown',
               }

def getMapValue(ob, datapoint, map):
    ''' attempt to map number to data dict'''
    try:
        value = int(ob.getRRDValue(datapoint))
        return map[value]
    except:
        return 'Unknown'

def getSiebelRunState(ob): return ob.getMapValue('status_runState', ob.siebelRunStateMap)


SiebelDefinition = type('SiebelDefinition', (BasicDefinition,), {
        'version' : VERSION,
        'zenpackbase': BASE,
        'packZProperties' : [
                            ('zSiebelGateway', 'GATEWAY', 'string'),
                            ('zSiebelEnterprise', 'ENTERPRISE', 'string'),
                            ('zSiebelUser', 'USER', 'string'),
                            ('zSiebelPassword', 'PASSWORD', 'password'),
                            ('zSiebelPerfCycleSeconds', 300, 'int'),
                            ('zSiebelPerfCyclesPerConnection', 288, 'int'),
                            ('zSiebelPerfTimeoutSeconds', 30, 'int'),
                            ('zSiebelShareGateway',True,'boolean')
                            ],
        'component' : 'SiebelComponent',
        'componentData' : {
                           'singular': 'Siebel Component',
                           'plural': 'Siebel Components',
                           'properties': { 
                                        'sv_name': addProperty('Server', optional=False),
                                        'gateway' : addProperty('Gateway'),
                                        'enterprise' : addProperty('Enterprise'),
                                        'cc_name': addProperty('CC Name', optional=False),
                                        'cg_alias' : addProperty('CG Alias', optional=False),
                                        'cc_alias' : addProperty('CC Alias'),
                                        'ct_alias' : addProperty('CT Alias', optional=False),
                                        'cp_startmode' : addProperty("CP Start Mode", optional=False),
                                        'cc_runmode': addProperty("CC Run Mode", optional=False),
                                        'cp_max_tasks': addProperty("CP Max Tasks"),
                                        'eventClass' : getEventClass('/App/Siebel'),
                                        'getSiebelRunState' : getReferredMethod('Run State', 'getSiebelRunState'),
                                        },
                           },
        'componentAttributes' : { 'siebelRunStateMap': siebelRunStateMap, },
        'componentMethods' : [getMapValue, getSiebelRunState ],
        'createDS' : True,
        'datasourceData' : {'properties': {'command': addProperty('Command'),}}
        }
)


addDefinitionSelfComponentRelation(SiebelDefinition,
                          'siebelcomponents', ToMany, '%s.%s.%s' % (ROOT, BASE, 'SiebelComponent'),'sv_name',
                          'winservice',  ToOne, 'Products.ZenModel.WinService', 'serviceName',
                          'Service', 'serviceName')

