import sys, os, re, pexpect
import Globals
from optparse import OptionParser
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.ZenUtils.Utils import zenPath,prepId
from twisted.internet.utils import getProcessOutput

class SiebelHandler():
    """ Class to handle input/output from srvrmgr for 
        a Zenoss device
    """
    
    def __init__(self):
        """ 
        """
        self.binPath = '/opt/zenoss/libexec/srvrmgr'
        self.status = 0
        self.message = ''
        
    def initialize(self,gateway=None,enterprise=None,server=None,user=None,password=None,timeout=120):
        """ initialize Siebel connection for Zenoss device
        """
        self.gateway = gateway
        self.enterprise = enterprise
        self.server = server
        self.user = user
        self.password = password
        self.connectString = self.binPath
        self.connectString += ' /g ' + self.gateway
        self.connectString += ' /e ' + self.enterprise
        self.connectString += ' /s ' + self.server
        self.connectString += ' /u ' + self.user
        self.connectString += ' /p ' + self.password
        self.timeout = timeout
        self.prompt = 'srvrmgr:'+self.server.upper()
        self.child = pexpect.spawn(self.connectString)
        try:
            self.child.expect(self.prompt, timeout=self.timeout)
            self.status = 0
            self.message = 'OK: Connected to '+self.server
        except:
            self.status = 1
            self.message = 'WARNING: could not connect to '+self.server
    
    def terminate(self):
        self.child.sendline('exit')
        self.child.close()
    
    def getCommandOutput(self,command):
        """ execute a command against srvrmgr and 
            return the data as a python dictionary
        """
        output = self.execCommand(command)
        data = self.parseOutput(output)
        return data
        
    def execCommand(self,command):
        """ execute a given srvrmgr command and wait
            for the prompt
        """
        try:
            self.child.sendline(command)
            self.child.expect(self.prompt, timeout=self.timeout)
            #self.message = 'OK: Query successful on '+self.server
            self.status = 0
            return self.child.before
        except:
            self.status = 1
            #self.message = 'WARNING: Query failed on '+self.server
            return None
        
    def parseOutput(self,data):
        """ convert the srvrmgr output to a python dictionary
        """
        lines = data.splitlines()
        datadict = {}
        headers = []
        rows = []

        # first find the data header, determine number of columns
        for i,line in enumerate(lines):
            # finish query if error detected
            if re.match('error code',line) or re.match('system error',line):
                self.status = 1
                self.message = 'WARNING: Query failed on '+self.server
                return datadict
                
            if line.startswith('----'): 
                headers = lines[i-1].split()

        for h in headers: # set up list entries for dictionary
            datadict[h] = []
            
        # next find the row data
        collect=False
        for i,line in enumerate(lines):
            if i == 0:
                continue
            if len(line) == 0:
                continue
            if line.startswith('----'):
                collect = True
                continue
            if collect == True:
                rowdata = line.split()
                if len(rowdata) == len(headers):
                    rows.append(rowdata)

        for row in rows: # now parse it into a dictionary structure  
            for i,header in enumerate(headers):
                datadict[header].append(row[i])
                
        return datadict                 
    
    def nagiosOutput(self,dictionary={},keyField=None,valueField=None):
        """ return nagios-style output
        """
        outputData = ''
        try:
            entries = len(dictionary[dictionary.keys()[0]])
            for i in range(entries):
                dataKey = dictionary[keyField][i]
                dataValue = dictionary[valueField][i]
                outputData += dataKey+'='+dataValue+' '
        except:
            pass
        return outputData
    
    def isServerRunning(self):
        """ determine if server is running
        """
        command = 'list servers show SBLSRVR_NAME,HOST_NAME,SBLSRVR_STATE,START_TIME,END_TIME'
        data = self.getCommandOutput(command)
        entries = len(data[data.keys()[0]])
        if entries == 0:
            return False
        else:
            for e in range(entries):
                siebelServer = data['SBLSRVR_NAME'][e]
                siebelState = data['SBLSRVR_STATE'][e]
                if siebelServer == self.server:
                    if siebelState != 'Running':
                        return False
        return True

class SiebelData():
    """ Class to collect specific Siebel-related data
    """
    def __init__(self,dmd):
        """ 
        """
        self.dmd = dmd
        self.siebel = SiebelHandler()
        self.updateStatus()
        self.runStatus = None
    
    def connect(self,device=None,timeout=120):
        """ initiate connection to Siebel server
        """
        self.device = self.dmd.Devices.findDeviceByIdOrIp(device)
        self.gateway = self.device.zSiebelGateway
        self.enterprise = self.device.zSiebelEnterprise
        self.server = self.device.zSiebelServer
        self.user = self.device.zSiebelUser
        self.password = self.device.zSiebelPassword
        self.siebel.initialize(self.gateway,self.enterprise,self.server,self.user,self.password,timeout)
        self.updateStatus()
    
    def disconnect(self):
        """ close connection to Siebel server
        """
        self.siebel.terminate()  
   
    def updateStatus(self):
        """ Update the nagios-style status,message attributes
        """
        #self.message = self.siebel.message
        self.status = self.siebel.status
      
    def checkQuery(self):
        """ Check to see that server connection is OK before proceeding
        """
        self.updateStatus()
        if self.siebel.status != 0:
            return False
        return True
    
    def getStatsForComponent(self,component):
        """ retrieve performance stats for an individual component
        """
        if self.checkQuery() == True:
            command = 'list statistics for component '+component+' show STAT_ALIAS,SD_DATATYPE,SD_SUBSYSTEM,CURR_VAL'
            data = self.siebel.getCommandOutput(command)
            self.updateStatus()
            self.message += '|'
            self.message += self.siebel.nagiosOutput(dictionary=data,keyField='STAT_ALIAS',valueField='CURR_VAL')
        return self.message
    
    def getTasksForComponent(self,component):
        """ retrieve task status for an individual component
        """
        if self.checkQuery() == True:
            numTasks = 0
            goodTasks = 0
            badTasks = 0
            try:
                command = 'list tasks for component '+component+' show SV_NAME, CC_ALIAS, TK_PID, TK_DISP_RUNSTATE'
                data = self.siebel.getCommandOutput(command)
                entries = len(data[data.keys()[0]])
                numTasks = entries
                for i in range(entries):
                    taskStatus = data['TK_DISP_RUNSTATE'][i].upper()
                    if taskStatus == 'RUNNING' or taskStatus == 'COMPLETED'  or taskStatus == 'ONLINE':
                        goodTasks += 1
                    else:
                        badTasks += 1
            except:
                pass
            #self.message += '|'
            self.message += 'numTasks='+str(numTasks)
            self.message += ' goodTasks='+str(goodTasks)
            self.message += ' badTasks='+str(badTasks)
        return self.message
    
    def getComponentRunStatus(self,component):
        """ find the run status of this component
        """
        command = 'list component '+component+' show CC_ALIAS,CP_DISP_RUN_STATE,CP_START_TIME,CP_END_TIME'
        if self.checkQuery() == True:
            data = self.siebel.getCommandOutput(command)
            try:
                runstate = data['CP_DISP_RUN_STATE'][0]
                if runstate == 'Online':
                    self.message += ' runState=2'
                elif runstate == 'Running':
                    self.message += ' runState=3'
                elif runstate == 'Unavailable':
                    self.message += ' runState=0'
                elif runstate == 'Stopped':
                    self.message += ' runState=1'
            except:
                self.message += ' runState=-1'
            return self.message   
        
    def setComponentStatus(self,component):
        """ retrieve and set the run status of all components
        """
        command = 'list component '+component+' show CC_ALIAS,CP_DISP_RUN_STATE,CP_START_TIME,CP_END_TIME'
        if self.checkQuery() == True:
            data = self.siebel.getCommandOutput(command)
            entries = len(data[data.keys()[0]])
            for i in range(entries):
                ccalias = data['CC_ALIAS'][i]
                runstate = data['CP_DISP_RUN_STATE'][i]
                startTime = data['CP_START_TIME'][i]
                endTime = data['CP_END_TIME'][i]
                for c in self.device.siebelComponents():
                    if c.CCalias == ccalias:
                        self.runStatus = runstate
                        c.runState = runstate
                        c.startTime = startTime
                        c.endTime = endTime

            
    
        
