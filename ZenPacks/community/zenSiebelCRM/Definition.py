from ZenPacks.community.ConstructionKit.Construct import *
from Products.ZenModel.migrate.Migrate import Version
import os

class Definition():
    """
    """
    version = Version(2, 0, 0)
    zenpackroot = "ZenPacks.community" # ZenPack Root
    zenpackbase = "zenSiebelCRM" # ZenaPack Name

    #dictionary of components
    component = 'SiebelComponent'
    componentData = {
                  'singular': 'Siebel Component',
                  'plural': 'Siebel Components',
                  'displayed': 'id', # component field in Event Console
                  'primaryKey': 'id',
                  'properties': { 
                        # Basic settings
                        'CGalias' : addProperty('CG Alias','Basic', optional='false'),
                        'CCalias': addProperty('CC Alias','Basic', optional='false'),
                        'runState' : addProperty('State','Basic', optional='false'),
                        'startTime' : addProperty('Start Time','Basic', optional='false'),
                        'endTime': addProperty('End Time','Basic',optional='false'),
                        },
                  }
    
    packZProperties = [
        ('zSiebelGateway', 'GATEWAY', 'string'),
        ('zSiebelEnterprise', 'ENTERPRISE', 'string'),
        ('zSiebelServer', 'SERVER', 'string'),
        ('zSiebelUser', 'USER', 'string'),
        ('zSiebelPassword', 'PASSWORD', 'password'),
        ('zSiebelPerfCycleSeconds', 300, 'int'),
        ('zSiebelPerfCyclesPerConnection', 288, 'int'),
        ('zSiebelPerfTimeoutSeconds', 10, 'int'),
        ('zSiebelShareGateway',True,'boolean')
        ]
    #dictionary of datasources
    addManual = False
    createDS = False
    provided = False
    cwd = os.path.dirname(os.path.realpath(__file__)) # ZenPack files directory
