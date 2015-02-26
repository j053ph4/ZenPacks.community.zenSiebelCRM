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
from Products.ZenEvents.Event import Warning, Clear, Error
from Products.ZenUtils.observable import ObservableMixin
from Products.ZenUtils.Utils import unused
from ZenPacks.community.zenSiebelCRM.lib.SiebelHandler import SiebelHandler
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
    ERROR_EVENT = dict(component="zensiebelperf", severity=Error, eventClass='/App/Siebel')
    
    WARNING_COMPONENT_EVENT = dict(severity=Warning, eventClass='/App/Siebel')
    CLEAR_COMPONENT_EVENT = dict(component="zensiebelperf", severity=Clear, eventClass='/App/Siebel')


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
        # for use in logging
        self._compId = None
        self._dsId = None
    
    def connectionInfo(self, session):
        """
            Return a basic message string used for logging
        """
        gtwy = session.gateway.upper()
        ent = session.enterprise.upper()
        count = len(session.clients)
        if count == 0:  count = 1
        age = int(session.timesRun / count)
        if session.connected is True: connected = 'CONNECTED'
        else:  connected = 'DISCONNECTED'
        if session.blocked is True:  blocked = 'BLOCKED'
        else:  blocked = 'CLEARED'
        return '%s : %s is %s and %s for use with %s clients after %s run cycles' % (ent, gtwy, connected, blocked, count,  age)
    
    def _reset(self):
        """ 
            Reset srvrmgr connection, terminate if needed
        """
        if self.siebelClient is not None and self.siebelClient.blocked is True: self.resetSession(self.siebelClient)
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
            
    def _connectFailure(self, result):
        """
        Errback for an unsuccessful asynchronous connection
        request.
        """
        err = result.getErrorMessage()
        if self.siebelClient is not None:
            msg = 'Error connecting to gateway: %s on enterprise: %s with error: "%s" and message: "%s"' % (self._taskConfig.zSiebelEnterprise, self._taskConfig.zSiebelGateway, err, self.siebelClient.message)
        else:
            msg = 'Error connecting to gateway: %s on enterprise: %s with error: "%s"' % (self._taskConfig.zSiebelEnterprise, self._taskConfig.zSiebelGateway, err)
        self._eventService.sendEvent(ZenSiebelTask.ERROR_EVENT, device=self._devId, summary=msg)
        log.error(msg)
        # test/reset the connection
        self.failedConnection(self.siebelClient)      
        return result
    
    def _collectFailure(self, result):
        """
        Errback for an unsuccessful asynchronous collection
        request.
        """
        err = result.getErrorMessage()
        if self.siebelClient is not None:
            msg = '%s datasource collection failed with error: "%s" and message: "%s"'  % (self._dsId, err, self.siebelClient.message)
        else:
            msg = '%s datasource collection failed with error: "%s"'  % (self._dsId, err)
        log.error(msg)
        self._eventService.sendEvent(ZenSiebelTask.WARNING_COMPONENT_EVENT, device=self._devId, component=self._compId, summary=msg)
        # test/reset the connection
        self.failedConnection(self.siebelClient)      
        return result
    
    def _connect(self):
        """
            Connect to the Siebel device asynchronously.
        """
        log.debug("Connecting to %s", self._devId)
        self.state = ZenSiebelTask.STATE_CONNECTING
        self.siebelClient = self.recycleConnection()
        # add to connection pool if needed
        if self.siebelClient not in self._preferences.siebelclients:  self._preferences.siebelclients.append(self.siebelClient)
        return self.configure()

    def _connectCallback(self, result):
        """
        Callback for a successful asynchronous connection request.
        """
        log.debug("Connected to %s", self._devId)
        self._eventService.sendEvent(ZenSiebelTask.CLEAR_EVENT, device=self._devId, summary="Device connected successfully")
       
    def _collectSuccessful(self, result):
        """
        Callback for a successful asynchronous performance data collection
        request.
        """
        #log.debug("Successful collection from %s [%s], result=%s",self._devId, self._manageIp, result)
        log.info("Collected %s datasources for %s", len(result.keys()), self._devId)
        for compId, dsDict in result.items():
            for dsId, compDict in dsDict.items():
                for dpId, dpValue in compDict.items():
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
                        log.exception("Unable to write for %s for device [%s]", pId, self._devId)
            self._eventService.sendEvent(ZenSiebelTask.CLEAR_COMPONENT_EVENT, device=self._devId, component=self._compId, summary="Device collected successfully")
        self.siebelClient.timesRun += 1
        #self._eventService.sendEvent(ZenSiebelTask.CLEAR_EVENT, device=self._devId, summary="Device collected successfully")
    
    def _collectCleanup(self, result):
        """
        Callback after a successful collection to perform any cleanup after the
        data has been processed.
        """
        log.info("Collection completed for %s" % self._devId)
        self.ageConnection()
        return defer.succeed(None)
        
    def _collectCallback(self, result):
        """
            Callback used to begin performance data collection asynchronously after
            a connection or task setup.
        """
        if self.siebelClient:
            self.state = ZenSiebelTask.STATE_COLLECTING
            log.info("Collecting data for %s" % self._devId)
            d = self.fetch()
            d.addCallbacks(self._collectSuccessful, self._collectFailure)
            d.addCallback(self._collectCleanup)
            return d
        
    def cleanup(self):
        """
            run when shutting daemon down
        """
        log.info("Cleaning up session for %s" % self._devId)
        self.setBlocked(self.siebelClient)
        self._reset()
    
    def doTask(self):
        """
            Data collection routine
        """
        log.info("Performing tasks for %s" % self._devId)
        # find a working connection in pool
        d = self._connect()
        d.addCallbacks(self._connectCallback, self._connectFailure)
        # collect data
        d.addCallback(self._collectCallback)
        d.addBoth(self._finished)
        return d
        
    def createConnection(self):
        """ create a new srvrmgr connection
        """
        session = SiebelHandler()
        session.initialize(self._taskConfig.zSiebelGateway, self._taskConfig.zSiebelEnterprise,
                           None, self._taskConfig.zSiebelUser, self._taskConfig.zSiebelPassword,
                           self._taskConfig.timeoutSeconds, True)
        log.info('Created connection to %s with message: "%s"' % (self.connectionInfo(session), session.message))
        # add the current device to the list of session clients
        if self._devId not in session.clients: session.clients.append(self._devId)
        return session
    
    def examineSessions(self):
        """ 
            Examine running sessions, determine which can be used
        """
        goodSessions = []
        # counting unblocked sessions
        unblockedSessions = 0
        # current number of sessions
        currentSessions = len(self._preferences.getSiebelClients())
        log.info("Examining %s active sessions for %s" % (currentSessions, self._devId))
        # first loop through sessions and try to kill any that are blocked/disconnected
        for index, session in enumerate(self._preferences.getSiebelClients()):
            # assume the connection is bad unless proven otherwise
            passed = False
            # defined for convenience in this method
            gtwy = session.gateway.upper()
            ent = session.enterprise.upper()
            count = len(session.clients)
            connected = session.connected
            blocked = session.blocked
            age = int(session.timesRun / count)
            # reusable log message
            base = self.connectionInfo(session)
            basemsg = 'connection %s to %s' % (index, base)
            log.debug('Evaluating %s' % basemsg)
            # retest a disconnected session to see if it can be salvaged
            if session.connected is False:
                # if it is not yet blocked, retest it
                if session.blocked is False:
                    # test the session for connectivity
                    session.testConnected()
                    # set session to blocked if it failed further testing
                    if session.connected is False: 
                        log.warn('Blocking %s since retest failed with message: "%s"' % (basemsg, session.message))
                        # set session to blocked
                        self.setBlocked(session)
                    else:
                        log.info('Passing %s since retest succeeded with message: "%s"' % (basemsg, session.message))
                        passed = True
                        #session.blocked = False # just making sure
                        unblockedSessions += 1
                # try resetting the session if it is still bad
                else: 
                    log.warn('Skipping %s since it is blocked with message: "%s"' % (basemsg, session.message))
                    # may not need to do this
                    self.resetSession(session)
            else: # session is OK
                if session.blocked is False: # connection not blocked due to age.
                    log.info('Passing %s' % basemsg)
                    unblockedSessions += 1
                    passed = True
                # session is blocked, most likely due to age
                else:
                    log.info('Skipping %s' % basemsg)
            if passed is True: goodSessions.append(session)
            else: self.resetSession(session)
        log.debug("%s of %s sessions passed examination", (len(goodSessions), currentSessions))
        return goodSessions

    def recycleConnection(self):
        """ 
            Determine if a srvrmgr session exists and can be used 
            or if a new one should be created
        """
        # first get only the good sessions
        sessions = self.examineSessions()
        log.debug("Examining %s existing sessions for use by %s", len(sessions), self._devId)
        # look through current sessions and try to reuse one
        for index, session in enumerate(sessions):
            base = self.connectionInfo(session)
            basemsg = 'connection %s to %s' % (index, base)
            # if session matches the connection parameters of this server
            if session.gateway.upper() == self._taskConfig.zSiebelGateway.upper() and session.enterprise.upper() == self._taskConfig.zSiebelEnterprise.upper():
                # if session is noat full, is connected, and is not blocked
                if len(session.clients) < self.maxPerGateway:
                    if session.connected is True:
                        if session.blocked is False:
                            log.info('Recycling existing %s for %s' % (basemsg, self._devId))
                            return session
        # if no sessions can be recycled, create a new one
        newsession = self.createConnection()
        base = self.connectionInfo(newsession)
        log.info('Creating new connection to %s for %s' % (base, self._devId))
        return newsession

    def configure(self):
        """
        """
        def inner(driver):
            #log.info("Finding connection for %s",self._devId)
            if self.siebelClient is not None:
                basemsg = self.connectionInfo(self.siebelClient)
                # this is a good connection
                if self.siebelClient.connected is True and self.siebelClient.blocked is False:
                    yield defer.succeed("%s using connection to %s" % (self._devId, basemsg))
                else:
                    yield defer.fail("%s could not find connection to %s" % (self._devId, basemsg))
        return drive(inner)
    
    def setBlocked(self, session):
        """
            blocked flag will prevent session from reuse in future polling cycles
        """
        if session is not None:
            if session.blocked is False:
                log.info('Blocking connection to %s' % self.connectionInfo(session))
                session.blocked = True
    
    def failedConnection(self, session):
        """ 
            deal with failed collection
        """
        basemsg  = self.connectionInfo(session)
        log.warn('Testing previously failed connection to %s for %s' % (basemsg, self._devId))
        if session is not None:
            # first test that session is still connected self._taskConfig.zSiebelServer
            session.connected = session.testSessionConnected()
            # session is OK
            if session.connected is True:
                log.info('Connection to %s passed with message: "%s"' % (basemsg, session.message))
            # session is disconnected, discontinue use 
            else:
                log.warn('Connection to %s failed with message: "%s"' % (basemsg, session.message))
                self.setBlocked(session)
                self.resetSession(session)
    
    def ageConnection(self):
        """
            test if connection has been used for too long
        """
        if self.siebelClient is not None:
            basemsg  = self.connectionInfo(self.siebelClient)
            count = len(self.siebelClient.clients)
            timesRun = int(self.siebelClient.timesRun / count)
            maxRun = self._taskConfig.cyclesPerConnection
            log.info('Testing age of connection to %s out of a maximum of %s' % (basemsg, maxRun))
            if timesRun >= maxRun:
                log.info('Aging out connection to %s' % basemsg)
                self.setBlocked(self.siebelClient)
        self._reset()
          
    def resetSession(self, session):
        """
            Terminate srvrmgr connection and remove from list of sessions
        """
        basemsg  = self.connectionInfo(session)
        log.info('Resetting connection to %s with message: "%s"' % (basemsg, session.message))
        if len(session.clients) > 0: # end the session only if no servers are still using it
            log.info('Waiting to reset because connection to %s is still in use' % basemsg)
            # remove the client from the connection clients list
            if self._devId in session.clients: 
                log.info('Dropping %s from connection to %s' % (self._devId, basemsg))
                session.clients.remove(self._devId)
                # try to reset again 
                self.resetSession(session)
        else: #  can safely terminate if not in use
            log.info('Reset proceeding for connection to %s' % basemsg)
            try:
                session.terminate()
                self._preferences.siebelclients.remove(session)
                log.info('Reset suceeded for connection to %s' % basemsg)
            except:
                log.warn('Reset failed for connection to %s with message: "%s"' % (basemsg, session.message))
    
    def fetch(self):
        """
            Main data collection routine, loops though data sources, updating each one
            after executing datasource commands
        """   
        def inner(driver):
            result = {}
            log.debug("Executing commands for %s (%s datasources)", self._devId,len(self._taskConfig.datasources.items()))
            for compId, dsDict in self._taskConfig.datasources.items():
                self._compId = compId
                result[compId] = {}
                log.debug("Collecting data for component: %s on device: %s",compId,self._devId)
                for dsId, compDict in dsDict.items():
                    self._dsId = dsId
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

if __name__ == '__main__':
    myPreferences = ZenSiebelPreferences()
    myTaskFactory = SimpleTaskFactory(ZenSiebelTask)
    myTaskSplitter = SimpleTaskSplitter(myTaskFactory)
    daemon = CollectorDaemon(myPreferences, myTaskSplitter)
    daemon.run()

