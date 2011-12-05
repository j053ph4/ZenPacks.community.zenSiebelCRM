import logging
log = logging.getLogger('zen.zensiebelperf')

import Globals
import zope.component
import zope.interface
from twisted.internet import defer
from twisted.python.failure import Failure
from Products.ZenCollector.daemon import CollectorDaemon
from Products.ZenCollector.interfaces import ICollectorPreferences, IScheduledTask, IEventService, IDataService
from Products.ZenCollector.tasks import SimpleTaskFactory, SimpleTaskSplitter, TaskStates
from Products.ZenUtils.observable import ObservableMixin
from Products.ZenUtils.Utils import unused
from ZenPacks.community.zenSiebelCRM.SiebelHandler import SiebelHandler
from ZenPacks.community.zenSiebelCRM.services.SiebelConfigService import SiebelConfigService

unused(Globals)
unused(SiebelConfigService)

from Products.ZenUtils.Driver import drive


class ZenSiebelPreferences(object):
    zope.interface.implements(ICollectorPreferences)

    def __init__(self):
        self.collectorName = 'zensiebelperf'
        self.configurationService = "ZenPacks.community.zenSiebelCRM.services.SiebelConfigService"

        self.cycleInterval = 5 * 60

        self.configCycleInterval = 5 * 60
        
        self.options = None

    def buildOptions(self, parser):
        """
        Required to implement the ICollectorPreferences interface.
        """
        pass

    def postStartup(self):
        """
        Required to implement the ICollectorPreferences interface.
        """
        pass


class ZenSiebelTask(ObservableMixin):
    zope.interface.implements(IScheduledTask)
    
    STATE_CONNECTING = 'CONNECTING'
    STATE_COLLECTING = 'COLLECTING'

    def __init__(self, taskName, deviceId, interval, taskConfig):
        super(ZenSiebelTask, self).__init__()
        self._taskConfig = taskConfig
        self._eventService = zope.component.queryUtility(IEventService)
        self._dataService = zope.component.queryUtility(IDataService)
        self._preferences = zope.component.queryUtility(
            ICollectorPreferences, 'zensiebelperf')

        self.name = taskName
        self.configId = deviceId
        self.interval = interval
        self.state = TaskStates.STATE_IDLE
        self.timeout = 120
        self._taskConfig = taskConfig
        self._devId = deviceId
        self._manageIp = self._taskConfig.manageIp
        self._srvrmgr = None
        
    def _connect(self):
        """
        Connect to the Siebel device asynchronously.
        """
        log.info("Connecting to %s [%s]", self._devId, self._manageIp)
        self.state = ZenSiebelTask.STATE_CONNECTING
        self._srvrmgr = SiebelHandler()
        return self.configure()
    
    def getTasks(self,data):
        """ retrieve task status for an individual component
        """
        numTasks = 0
        goodTasks = 0
        badTasks = 0
        try:
            entries = len(data[data.keys()[0]])
            numTasks = entries
            for i in range(entries):
                taskStatus = data['TK_DISP_RUNSTATE'][i].upper()
                if (taskStatus == 'RUNNING' or taskStatus == 'COMPLETED'  or taskStatus == 'ONLINE'):
                    goodTasks += 1
                else:
                    badTasks += 1
        except:
            pass
        return numTasks,goodTasks,badTasks
    
    def getRunState(self,data):
        """ find the run status of this component
        """
        try:
            runstate = data['CP_DISP_RUN_STATE'][0]
            if runstate == 'Online':
                return 2
            elif runstate == 'Running':
                return 3
            elif runstate == 'Unavailable':
                return 0
            elif runstate == 'Stopped':
                return 1
        except:
            return -1
        
    def configure(self):
        def inner(driver):
            # initialize the connection
            self._srvrmgr.initialize(self._taskConfig.zSiebelGateway,
                                 self._taskConfig.zSiebelEnterprise,
                                 self._taskConfig.zSiebelServer,
                                 self._taskConfig.zSiebelUser,
                                 self._taskConfig.zSiebelPassword,
                                 self.timeout)
            log.debug("Configuring connection with %s",self._srvrmgr.connectString)
            if self._srvrmgr.status == 0:
                self.connected = True
                yield defer.succeed(None)
            else:
                self.connected = False
                yield defer.failed()
        return drive(inner)
    
    def fetch(self):
        log.info("Executing commands for %s [%s] (%d datasources)",
                  self._devId, self._manageIp,len(self._taskConfig.datasources.items()))
        def inner(driver):
            result = {}
            for compId,dsDict in self._taskConfig.datasources.items():
                result[compId] = {}
                for dsId,compDict in dsDict.items():
                    command = compDict['command']
                    sourcetype = compDict['sourcetype']
                    output = self._srvrmgr.getCommandOutput(command)
                    result[compId][dsId] = {}
                    if sourcetype == 'SiebelStatus':
                        runState = self.getRunState(output)
                        result[compId][dsId]['runState'] = runState
                    if sourcetype == 'SiebelTasks':
                        numTasks,goodTasks,badTasks = self.getTasks(output)
                        result[compId][dsId]['numTasks'] = numTasks
                        result[compId][dsId]['goodTasks'] = goodTasks
                        result[compId][dsId]['badTasks'] = badTasks
                    if sourcetype == 'SiebelPerf':
                        dataItems = self._srvrmgr.statDict(output,'STAT_ALIAS','CURR_VAL')
                        for dpId,dpValue in dataItems.items():
                            result[compId][dsId][dpId] = dpValue
                                 
            yield defer.succeed(result)
        return drive(inner)
    
    def fetchTasks(self,compId):
        """
        """
        log.info("Fetching task status for %s %s",
                  self._devId, compId)
        numTasks = 0
        goodTasks = 0
        badTasks = 0
        tasks = {}
        try:
            command = 'list tasks for component '+compId+' show SV_NAME, CC_ALIAS, TK_PID, TK_DISP_RUNSTATE'
            output = self._srvrmgr.getCommandOutput(command)
            print "output",output
            entries = len(output[output.keys()[0]])
            print "entries",entries
            numTasks = entries
            for i in range(entries):
                taskStatus = output['TK_DISP_RUNSTATE'][i].upper()
                if taskStatus == 'RUNNING' or taskStatus == 'COMPLETED'  or taskStatus == 'ONLINE':
                    goodTasks += 1
                else:
                    badTasks += 1
        except:
            pass
        tasks['numTasks'] = numTasks
        tasks['goodTasks'] = goodTasks
        tasks['badTasks'] = badTasks
        return tasks
    
    def doTask(self):
        log.debug("Scanning device %s [%s]", self._devId, self._manageIp) 
        if not self._srvrmgr:
            d = self._connect()
            d.addCallbacks(self._connectCallback, self._failure)
        else:
            d = defer.Deferred()
            reactor.callLater(0, d.callback, None)

        d.addCallback(self._collectCallback)
        d.addBoth(self._finished)
        return d
    
    def cleanup(self):
        pass
    
    def _connectCallback(self, result):
        """
        Callback for a successful asynchronous connection request.
        """
        log.debug("Connected to %s [%s]", self._devId, self._manageIp)
        
    def _failure(self, result):
        """
        Errback for an unsuccessful asynchronous connection or collection
        request.
        """
        err = result.getErrorMessage()
        log.error("Unable to scan device %s: %s", self._devId, err)
        self._reset()
        return result
    
    def _reset(self):
        """
        Reset the srvrmgr connection and collection stats so that collection
        can start over from scratch.
        """
        log.debug("Resetting connection to %s",self._devId) 
        if self._srvrmgr:
          self._srvrmgr.terminate()
        self._srvrmgr = None
        return defer.succeed(None)

    def _collectSuccessful(self, result):
        """
        Callback for a successful asynchronous performance data collection
        request.
        """
        log.debug("Successful collection from %s [%s], result=%s",
                  self._devId, self._manageIp, result)
        
        for compId,dsDict in result.items():
            for dsId,compDict in dsDict.items():
                for dpId,dpValue in compDict.items():
                    try:
                        dpDict = self._taskConfig.datasources[compId][dsId][dpId]
                        self._dataService.writeRRD(dpDict['path'],
                                                    dpValue,
                                                    dpDict['rrdType'],
                                                    rrdCommand=dpDict['rrdCmd'],
                                                    cycleTime=self.interval,
                                                    min=dpDict['minv'],
                                                    max=dpDict['maxv'])
                    except Exception:
                        log.exception("Unable to write datapoint for command [%s] on device %s [%s]",
                                      compDict['command'], self._devId, self._manageIp)
                        
        log.debug("Successful scan of %s [%s] (%d datasources)",
                  self._devId, self._manageIp,len(result.keys()))
        
    def _collectSuccessfulNew(self, result):
        """
        Callback for a successful asynchronous performance data collection
        request.
        """
        log.debug("Successful collection from %s [%s], result=%s",
                  self._devId, self._manageIp, result)
        
        for compId,dsDict in result.items():
            for dsId,compDict in dsDict.items():
                for dpId,dpValue in compDict.items():
                    try:
                        dpc = self._taskConfig.datasources[compId][dsId][dpId]
                        self._dataService.writeRRD(dpc.rrdPath,
                                                    dpValue,
                                                    dpc.rrdType,
                                                    dpc.rrdCreateCommand,
                                                    cycleTime=self.interval,
                                                    min=dpc.rrdMin,
                                                    max=dpc.rrdMax)
                    except Exception:
                        log.exception("Unable to write datapoint for command [%s] on device %s [%s]",
                                      compDict['command'], self._devId, self._manageIp)
                        
        log.debug("Successful scan of %s [%s] (%d datasources)",
                  self._devId, self._manageIp,len(result.keys()))
        
    def _collectCallback(self, result):
        """
        Callback used to begin performance data collection asynchronously after
        a connection or task setup.
        """
        if self._srvrmgr:
            self.state = ZenSiebelTask.STATE_COLLECTING
            log.debug("Collecting data for %s [%s]", self._devId,
                      self._manageIp)
            d = self.fetch()
            d.addCallbacks(self._collectSuccessful, self._failure)

            return d
            
    def _finished(self, result):
        if not isinstance(result, Failure):
            log.debug("Successful scan of %s [%s] completed", 
                      self._devId, self._manageIp)
        else:
            log.debug("Unsuccessful scan of %s [%s] completed, result=%s",
                      self._devId, self._manageIp, result.getErrorMessage())
        return self._reset()
    
        
if __name__ == '__main__':
    myPreferences = ZenSiebelPreferences()
    myTaskFactory = SimpleTaskFactory(ZenSiebelTask)
    myTaskSplitter = SimpleTaskSplitter(myTaskFactory)
    daemon = CollectorDaemon(myPreferences, myTaskSplitter)
    daemon.run()

