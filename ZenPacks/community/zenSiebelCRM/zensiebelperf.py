import logging
log = logging.getLogger('zen.zensiebelperf')

import Globals
import zope.component
import zope.interface
from twisted.internet import base, defer, reactor
from twisted.python.failure import Failure
from Products.ZenCollector.daemon import CollectorDaemon
from Products.ZenCollector.interfaces import ICollectorPreferences, IScheduledTask, IEventService, IDataService
from Products.ZenCollector.tasks import SimpleTaskFactory, SimpleTaskSplitter, TaskStates
from Products.ZenEvents.Event import Warning, Clear
from Products.ZenUtils.observable import ObservableMixin
from Products.ZenUtils.Utils import unused
from ZenPacks.community.zenSiebelCRM.SiebelHandler import SiebelHandler
from ZenPacks.community.zenSiebelCRM.services.SiebelConfigService import SiebelConfigService
from Products.ZenUtils.Driver import drive

unused(Globals)
unused(SiebelConfigService)


class ZenSiebelPreferences(object):
    zope.interface.implements(ICollectorPreferences)

    def __init__(self):
        self.collectorName = 'zensiebelperf'
        self.configurationService = "ZenPacks.community.zenSiebelCRM.services.SiebelConfigService"
        self.cycleInterval = 300 # seconds
        self.configCycleInterval = 20 # minutes
        self.options = None
        self.siebelclients = []

    def buildOptions(self, parser):
        """
        Required to implement the ICollectorPreferences interface.
        """

        parser.add_option('--maxPerGateway', dest='maxPerGateway',
                        default=8, type='int',
                        help='Number of servers using a single srvrmgr session'
                        )

    def postStartup(self):
        """
        Required to implement the ICollectorPreferences interface.
        """
        pass
    
    def getSiebelClients(self):
        return self.siebelclients

    def maxPerGateway(self):
        return self.options.maxPerGateway

class ZenSiebelTask(ObservableMixin):
    zope.interface.implements(IScheduledTask)

    STATE_CONNECTING = 'CONNECTING'
    STATE_COLLECTING = 'COLLECTING'
    CLEAR_EVENT = dict(component="zensiebelperf", severity=Clear, eventClass='/App/Siebel')
    WARNING_EVENT = dict(component="zensiebelperf", severity=Warning, eventClass='/App/Siebel')

    def __init__(self, taskName, deviceId, interval, taskConfig):
        super(ZenSiebelTask, self).__init__()
        self._taskConfig = taskConfig
        self._eventService = zope.component.queryUtility(IEventService)
        self._dataService = zope.component.queryUtility(IDataService)
        self._preferences = zope.component.queryUtility(ICollectorPreferences, 'zensiebelperf')
        self.maxPerGateway = self._preferences.maxPerGateway()
        
        # All of these properties are required to implement the IScheduledTask
        # interface
        self.name = taskName
        self.configId = deviceId
        self.interval = interval
        self.state = TaskStates.STATE_IDLE
        
        # these will be used commonly throughout
        self._devId = deviceId
        self._manageIp = self._taskConfig.manageIp
        self.siebelClient = None
        self._reset()

    def _reset(self):
        """
        Reset srvrmgr connection, terminate if needed
        """
        if self.siebelClient and self.siebelClient.blocked == True:
                self.resetSession(self.siebelClient)
        self.siebelClient = None   
        return defer.succeed(None)

    def _finished(self, result):
        """ 
            post collection activities
        """
        if not isinstance(result, Failure):
            log.debug("Successful scan of %s completed", self._devId)
        else:
            log.error("Unsuccessful scan of %s completed, result=%s", self._devId, result.getErrorMessage())
        return result
            
    def _failure(self, result):
        """
        Errback for an unsuccessful asynchronous connection or collection
        request.
        """
        err = result.getErrorMessage()
        log.error("Unable to scan device %s: %s", self._devId, err)
        self.failedConnection(self.siebelClient)
        self._eventService.sendEvent(ZenSiebelTask.WARNING_EVENT, device=self._devId, summary="Error collecting performance data: %s" % err)
        return result

    def _connect(self):
        """
            Connect to the Siebel device asynchronously.
        """
        log.debug("Connecting to %s", self._devId)
        self.state = ZenSiebelTask.STATE_CONNECTING
        self.siebelClient = self.recycleConnection()
        if self.siebelClient not in self._preferences.siebelclients:
            self._preferences.siebelclients.append(self.siebelClient)
        return self.configure()

    def _connectCallback(self, result):
        """
        Callback for a successful asynchronous connection request.
        """
        log.debug("Connected to %s", self._devId)
        
    def _collectSuccessful(self, result):
        """
        Callback for a successful asynchronous performance data collection
        request.
        """
        #log.debug("Successful collection from %s [%s], result=%s",self._devId, self._manageIp, result)
        log.info("Successful collection of %s (%s datasources)",
                  self._devId, len(result.keys()))
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
                    except:
                        log.exception("Unable to write for %s for device [%s]",
                                      dpId, self._devId)
        self.siebelClient.timesRun += 1
        self._eventService.sendEvent(ZenSiebelTask.CLEAR_EVENT, device=self._devId, summary="Device collected successfully")

    def _collectCleanup(self, result):
        """
        Callback after a successful collection to perform any cleanup after the
        data has been processed.
        """
        
        log.info("Post-collect cleanup for %s, run %s times",self._devId,self.siebelClient.timesRun)
        self.ageConnection()
        return defer.succeed(None)
        
    def _collectCallback(self, result):
        """
            Callback used to begin performance data collection asynchronously after
            a connection or task setup.
        """
        if self.siebelClient:
            self.state = ZenSiebelTask.STATE_COLLECTING
            log.info("Collecting data for %s", self._devId)
            d = self.fetch()
            d.addCallbacks(self._collectSuccessful, self._failure)
            d.addCallback(self._collectCleanup)
            return d
        
    def cleanup(self):
        """
            run when shutting daemen down
        """
        log.info("Cleaning up session for %s",self._devId)
        self.setBlocked(self.siebelClient)
        self._reset()
    
    def doTask(self):
        """
            Data collection routine
        """
        #import gc
        #gc.collect()
        log.info("Scanning device %s", self._devId)
        d = self._connect()
        d.addCallbacks(self._connectCallback, self._failure)
        
        d.addCallback(self._collectCallback)
        d.addBoth(self._finished)
        return d
    
    def getTasks(self,data=[]):
        """ retrieve task status for an individual component
        """
        log.info("Collecting Task data for for %s",self._devId)
        goodTasks = 0
        numTasks = len(data)
        goodStatus = ['RUNNING','COMPLETED','ONLINE']
        for d in data:
            try:
                taskStatus = d['TK_DISP_RUNSTATE'].upper()
            except:
                taskStatus = 'UNKNOWN'
            if taskStatus in goodStatus:   
                goodTasks += 1
        badTasks = numTasks - goodTasks
        return numTasks,goodTasks,badTasks
    
    def getRunState(self,data):
        """ find the run status of this component
        """
        log.debug("Collecting Run State for for %s",self._devId)
        runStateMap = {
               'Running': 4,
               'Online': 3,
               'Unavailable': 2,
               'Stopped': 1,
               'Shutdown': 0,
               }
        try:
            runstate = data['CP_DISP_RUN_STATE']
            statenum = runStateMap[runstate]
        except:
            statenum = -1
        return statenum
        
    def createConnection(self):
        """ create a new srvrmgr connection
        """
        log.debug("Creating new session for G: %s and E: %s with SHARING: %s and TIMEOUT: %s",
                 self._taskConfig.zSiebelGateway.upper(),
                 self._taskConfig.zSiebelEnterprise.upper(),
                 True,
                 self._taskConfig.timeoutSeconds)
        session = SiebelHandler()
        session.initialize(self._taskConfig.zSiebelGateway,
                           self._taskConfig.zSiebelEnterprise,
                           None,
                           self._taskConfig.zSiebelUser,
                           self._taskConfig.zSiebelPassword,
                           self._taskConfig.timeoutSeconds,
                           True)
        log.debug("Session created for G: %s and E: %s with the message: %s",
                 self._taskConfig.zSiebelGateway.upper(),
                 self._taskConfig.zSiebelEnterprise.upper(),
                 session.message)
        if self._devId not in session.clients:
            session.clients.append(self._devId)
        return session
 
    def examineSessions(self):
        """ 
            Examine running sessions, determine which can be used
        """
        log.debug("Examining %s active sessions for use by %s",len(self._preferences.siebelclients),self._devId)
        
        goodSessions = []
        # counting unblocked sessions
        unblockedSessions = 0
        # first loop through sessions and try to kill any that are blocked/disconnected
        for index,session in enumerate(self._preferences.getSiebelClients()):
            passed = False
            log.debug("Evaluating session %s to G: %s and E: %s with %s servers",
                     index,
                     session.gateway.upper(),
                     session.enterprise.upper(),
                     len(session.clients))
            if session.connected == False:
                log.warn("Session %s to G: %s and E: %s with %s servers failed previously with the message: %s",
                                index,
                                session.gateway.upper(),
                                session.enterprise.upper(),
                                len(session.clients),
                                session.message)
                # perform another test to see if the connection is OK
                if session.blocked == False:
                    log.warn("Testing session %s to G: %s and E: %s with %s servers",
                            index,
                            session.gateway.upper(),
                            session.enterprise.upper(),
                            len(session.clients))
                    # test the session for connectivity
                    session.testConnected()
                    # set session to blocked if it failed further testing
                    if session.connected == False: 
                        log.warn("    FAILED test of session %s to G: %s and E: %s with %s servers with message: %s",
                                index,
                                session.gateway.upper(),
                                session.enterprise.upper(),
                                len(session.clients),
                                session.message)
                        # set session to blocked
                        self.setBlocked(session)
                    else:
                        log.warn("    SUCCEEDED test of session %s to G: %s and E: %s with %s servers with message: %s",
                                index,
                                session.gateway.upper(),
                                session.enterprise.upper(),
                                len(session.clients),
                                session.message)
                        passed = True
                        #session.blocked = False # just making sure
                        unblockedSessions += 1
                        
                else: # try resetting the session if it is still bad
                    log.warn("    Skipping BLOCKED session %s to G: %s and E: %s with %s servers with message: %s",
                            index,
                            session.gateway.upper(),
                            session.enterprise.upper(),
                            len(session.clients),
                            session.message)
                    #self.resetSession(session)

            else: # session is OK
                if session.blocked == False: # connection not blocked due to age.
                    unblockedSessions += 1
                    log.debug("    Session %s to G: %s and E: %s with %s servers passed with message: %s",
                             index,
                             session.gateway.upper(),
                             session.enterprise.upper(),
                             len(session.clients),
                             session.message)
                    passed = True
                
            if passed == True:
                goodSessions.append(session)
            else:
                self.resetSession(session)
                
        log.debug("%s sessions passed examination",len(goodSessions))  
        return goodSessions

    def recycleConnection(self):
        """ 
            Determine if a srvrmgr session exists and can be used 
            or if a new one should be created
        """

        sessions = self.examineSessions()
        log.debug("Recycling %s sessions for use by %s",len(sessions),self._devId)
        for index,session in enumerate(sessions): # look through current sessions and try to reuse one       
            # if session matches the connection parameters of this server
            if session.gateway.upper() == self._taskConfig.zSiebelGateway.upper() and session.enterprise.upper() == self._taskConfig.zSiebelEnterprise.upper():
                # if session is noat full, is connected, and is not blocked
                if len(session.clients) < self.maxPerGateway:
                    if session.connected == True:
                        if session.blocked == False:
                            log.debug("    Device %s using session %s to G: %s and E: %s shared by %s servers", 
                                    self._devId,
                                    index,
                                    session.gateway.upper(),
                                    session.enterprise.upper(),
                                    len(session.clients))
                            return session
                        else:
                            log.warn("    Session %s is blocked, evaluating next session" % index)
                    
        log.warn("    Device %s found no available connection to G: %s and E: %s",
                 self._devId,
                 self._taskConfig.zSiebelGateway.upper(),
                 self._taskConfig.zSiebelEnterprise.upper())
        # if no sessions can be recycled, create a new one
        return self.createConnection()

    def configure(self):
        """
        """
        def inner(driver):
            log.info("Finding connection for %s",self._devId)
            log.debug("Current Client Connected: %s Blocked: %s" % (self.siebelClient.connected,self.siebelClient.blocked))
            if self.siebelClient.connected == True and self.siebelClient.blocked == False:
                yield defer.succeed(None)
            else:
                yield defer.fail("Could not find connection for %s" % self._devId)
        return drive(inner)
    
    def setBlocked(self,session):
        """
            blocked flag will prevent session from reuse in future polling cycles
        """
        try:
            if session.blocked == False:
                log.warn("Setting session BLOCKED to TRUE for G: %s and E: %s with message: %s",
                            session.gateway.upper(),
                            session.enterprise.upper(),
                            session.message)
                session.blocked = True
        except:
            pass
        
    def failedConnection(self,session):
        """ 
            deal with failed collection
        """
        log.warn("Post-failure test of SRVRMGR session to G: %s shared by %s servers for %s",session.gateway.upper(),len(self.siebelClient.clients),self._devId)
        if session:
            # first test that session is still connected self._taskConfig.zSiebelServer
            session.connected = session.testSessionConnected()
            if session.connected == True:
                log.warn("SRVRMGR session to G: %s E: %s shared by %s servers CONNECTED with message: %s", 
                             session.gateway.upper(),
                             session.enterprise.upper(),
                             len(session.clients),
                             session.message)
            else: # session is disconnected, discontinue use
                log.warn("SRVRMGR session to G: %s E: %s shared by %s servers FAILED with message: %s", 
                             session.gateway.upper(),
                             session.enterprise.upper(),
                             len(session.clients),
                             session.message)
                self.setBlocked(session)
                self.resetSession(session)
            
    def ageConnection(self):
        """
            test if connection has been used for too long
        """
        denom = len(self.siebelClient.clients)
        timesRun = int(self.siebelClient.timesRun / denom)
        log.debug("Testing calculated age %s against max age %s for session run %s times",timesRun,self._taskConfig.cyclesPerConnection,self.siebelClient.timesRun)
        if timesRun > self._taskConfig.cyclesPerConnection:
            log.debug("Max connection age %s reached after %s cycles for G: %s and E: %s", 
                     self._taskConfig.cyclesPerConnection, 
                     timesRun,
                     self.siebelClient.gateway.upper(),
                     self.siebelClient.enterprise.upper())
            self.setBlocked(self.siebelClient)
        self._reset()
          
    def resetSession(self,session):
        """
            Terminate srvrmgr connection and remove from list of sessions
        """
        log.debug("Attempting to reset session to G: %s shared by %s servers with message: %s",session.gateway.upper(),len(session.clients),session.message)
        if len(session.clients) > 0: # end the session only if no servers are still using it
            log.warn("Reset cannot proceed because G: %s still shared by %s servers",session.gateway.upper(),len(session.clients))
            self.dropServer(session)
        
        else: #  can safely terminate if not in use
            log.debug("Reset can proceed since G: %s is not in use",session.gateway.upper())
            try:
                session.terminate()
                self._preferences.siebelclients.remove(session)
                log.debug("Termination of session to G: %s E: %s SUCCEEDED",
                         session.gateway.upper(),
                         session.enterprise.upper())
            except:
                log.warn("Termination of session to G: %s E: %s FAILED with message: %s",
                         session.gateway.upper(),
                         session.enterprise.upper(),
                         session.message)
        
    def dropServer(self,session):
        """
            if blocked, reduce the number of servers using this connection
        """
        #if session.blocked == True:
        if self._devId in session.clients:
            session.clients.remove(self._devId)
        log.debug("Removing S: %s from blocked session to G: %s shared by  %s servers",
                self._devId,
                session.gateway.upper(),
                len(session.clients))
        if len(session.clients) == 0: # set disconnected flag if not used
            log.debug("Session to G: %s is unused (%s servers remaining).  OK to disconnect",
                     session.gateway.upper(),
                     len(session.clients))
            
    def fetch(self):
        """
            Main data collection routine, loops though data sources, updating each one
            after executing datasource commands
        """   
        def inner(driver):
            result = {}
            log.debug("Executing commands for %s (%s datasources)", self._devId,len(self._taskConfig.datasources.items()))
            for compId,dsDict in self._taskConfig.datasources.items():
                result[compId] = {}
                log.debug("Collecting data for component: %s on device: %s",compId,self._devId)
                for dsId,compDict in dsDict.items():
                    result[compId][dsId] = {}
                    command = compDict['command']
                    sourcetype = compDict['sourcetype']
                    log.debug("Executing command: %s for type: %s",command,sourcetype)
                    output = self.siebelClient.getCommandOutput(command)
                    if len(output) == 1 and 'CP_DISP_RUN_STATE' in command:
                        result[compId][dsId]['runState'] = self.getRunState(output[0])
                    elif 'list tasks' in command:
                        numTasks,goodTasks,badTasks = self.getTasks(output)
                        result[compId][dsId]['numTasks'] = numTasks
                        result[compId][dsId]['goodTasks'] = goodTasks
                        result[compId][dsId]['badTasks'] = badTasks
                    else:
                        dataItems = self.siebelClient.statDict(output,'STAT_ALIAS','CURR_VAL')
                        for dpId,dpValue in dataItems.items():
                            result[compId][dsId][dpId] = dpValue
            yield defer.succeed(result)
        return drive(inner)
     
if __name__ == '__main__':
    myPreferences = ZenSiebelPreferences()
    myTaskFactory = SimpleTaskFactory(ZenSiebelTask)
    myTaskSplitter = SimpleTaskSplitter(myTaskFactory)
    daemon = CollectorDaemon(myPreferences, myTaskSplitter)
    daemon.run()

