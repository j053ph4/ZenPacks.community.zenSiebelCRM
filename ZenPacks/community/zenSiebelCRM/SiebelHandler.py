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
        except:
            pass
            self.status = 1
    
    def terminate(self):
        """ end the srvrmgr connection
        """
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
            self.status = 0
            return self.child.before
        except:
            self.status = 1
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


