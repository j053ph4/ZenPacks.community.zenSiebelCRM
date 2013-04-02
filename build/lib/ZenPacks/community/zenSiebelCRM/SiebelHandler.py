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
        # path to the executable
        self.binPath = zenPath('libexec') + '/srvrmgr'
        self.connected = False
        self.blocked = False
        # number of servers currently sharing this srvrmgr session
        self.servers = 0
        # number of times the session has been run
        self.timesRun = 0
        # list of servers currently using this session.
        self.clients= []
        self.message = 'UNINITIALIZED'
        
    def initialize(self,gateway=None,enterprise=None,server=None,user=None,password=None,timeout=120,useGateway=False):
        """ initialize Siebel connection for Zenoss device
        """
        self.gateway = gateway
        self.enterprise = enterprise
        self.server = server
        self.user = user
        self.password = password
        self.useGateway = useGateway
        self.connectString = self.binPath
        self.connectString += ' /g ' + self.gateway.upper()
        self.connectString += ' /e ' + self.enterprise.upper()
        self.prompt = 'srvrmgr'
        if self.useGateway == False:
            self.connectString += ' /s ' + self.server.upper()
            self.prompt = 'srvrmgr:'+self.server.upper()
        self.connectString += ' /u ' + self.user
        self.connectString += ' /p ' + self.password
        self.timeout = timeout
        self.child = pexpect.spawn(self.connectString)
        self.testConnected()

    def testConnected(self):
        """ 
            Examine prompt to determine connection status
        """
        try:
            reply = self.child.expect([self.prompt,pexpect.EOF,pexpect.TIMEOUT], timeout=self.timeout)
            if reply == 0:
                self.connected = True
                #self.blocked = False
                self.message = "CONNECTION OK"
            elif reply == 1:
                self.message = "CONNECTION EOF"
                self.connected = False
            elif reply == 2:
                self.message = "CONNECTION TIMEOUT"
                self.connected = False
            else:
                self.message = "CONNECTION UNKNOWN"
                self.connected = False
        except:
            self.connected = False
            self.message = 'CONNECTION FAILED'
    
    def testSessionConnected(self):
        """
            return True if connected
        """
        if self.connected == False and self.blocked == True:
            return False
        command = "list servers show SBLSRVR_NAME,SBLSRVR_STATE"
        try:
            output = self.getCommandOutput(command)
            if len(output.items()) > 0:
                return True
        except:
            pass
        return False

    def testServerConnected(self,server):
        """
            return True if given server is connected
        """
        command = "list server " + server + " show SBLSRVR_NAME,SBLSRVR_STATE"
        output = self.getCommandOutput(command)
        try:
            if output['SBLSRVR_STATE'][0] == "Running":
                return True
        except:
            pass
        return False

    def terminate(self):
        """ end the srvrmgr connection
        """
        try:
            self.child.sendline('exit')
            self.child.close(force=True)
        except:
            pass
        self.child.terminate(force=True)  
        self.connected = False
    
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
            self.testConnected()
            if self.connected == True:
                return self.child.before
            else:
                return None
        except:
            return None

    def parseOutput(self,data):
        """ convert the srvrmgr output to a python dictionary
        """
        
        space = re.compile(r'\s+')
        try:
            lines = data.splitlines()
        except:
            lines = []
        datadict = {}
        headers = []
        rows = []

        # first find the data header, determine number of columns
        for i,line in enumerate(lines):
            # finish query if error detected
            if re.match('error code',line) or re.match('system error',line):
                self.status = 1
                return datadict
            if line.startswith('----'): 
                headers = lines[i-1].split()

        for h in headers: # set up list entries for dictionary
            datadict[h] = []
            
        # next find the row data
        collect=False
        for i,line in enumerate(lines):
            if i == 0:
                collect=False
                continue
            if len(line) == 0:
                collect=False
                continue
                
            if line.startswith('----'):
                collect = True
                continue
            if collect == True:
                rowdata = line.split()
                if len(rowdata) == len(headers):
                    rows.append(rowdata)
                elif len(rowdata) > len(headers):
                    while len(rowdata) > len(headers):
                        rowdata[0] += " "+rowdata[1]
                        rowdata.remove(rowdata[1])
                    rows.append(rowdata)
                else:
                    continue
                    
        for row in rows: # now parse it into a dictionary structure  
            for i,header in enumerate(headers):
                datadict[header].append(row[i])
                
        return datadict                 
    
    def statDict(self,dictionary={},keyField=None,valueField=None):
        """ return nagios-style output
        """
        newDict = {}
        try:
            entries = len(dictionary[dictionary.keys()[0]])
            for i in range(entries):
                dataKey = dictionary[keyField][i]
                dataValue = dictionary[valueField][i]
                newDict[dataKey] = dataValue
        except:
            pass
        return newDict
    
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


