import logging
log = logging.getLogger('zen.zenhub')
import sys, os, re, pexpect
import Globals
from optparse import OptionParser
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.ZenUtils.Utils import zenPath,prepId
from twisted.internet.utils import getProcessOutput


class SiebelHandler():
    """ Handler for srvrmgr session """
    def __init__(self):
        """"""
        self.cmd = '%s/srvrmgr' % zenPath('libexec') # path to the executable'
        self.connected = False
        self.blocked = False
        self.servers = 0 # number of servers currently sharing this srvrmgr session
        self.timesRun = 0 # number of times the session has been run
        self.clients= [] # list of servers currently using this session.
        self.message = 'UNINITIALIZED'
    
    def initialize(self,gateway=None,enterprise=None,server=None,user=None,password=None,timeout=30,useGateway=False):
        """ initialize Siebel connection for Zenoss device """
        self.gateway = gateway
        self.enterprise = enterprise
        self.server = server
        self.user = user
        self.password = password
        self.useGateway = useGateway
        self.args = ['/g %s' % self.gateway.upper(), '/e %s' % self.enterprise.upper(),'/u %s' % self.user, '/p %s' % self.password]
        self.prompt = 'srvrmgr'
        if self.useGateway == False:
            self.args.append('/s %s' % self.server.upper())
            self.prompt += ':%s' % self.server.upper()
        self.prompt += '> '
        self.connectString = '%s %s' % (self.cmd, ' '.join(self.args))
        self.timeout = timeout
        self.connect()
    
    def connect(self):
        ''' connect to gateway'''
        log.debug('connecting using %s' % self.connectString)
        self.child = pexpect.spawn(self.connectString)
        #fout = file('mylog.txt','w')
        #self.child.logfile = fout
        self.getExpect(self.prompt)
        self.testConnected()
        self.sendCommand('set delimiter |')
        
    def terminate(self):
        """ end the srvrmgr connection """
        log.debug('terminating connection using %s' % self.connectString)
        try:
            self.child.sendline('exit')
            self.child.expect('Disconnecting from server.')
            self.child.close(force=True)
        except:
            pass
        self.child.terminate(force=True)  
        self.connected = False
    
    def sendCommand(self, command):
        '''send a command to srvrmgr'''
        log.debug('sending command: %s' % command)
        self.child.sendline(command)
        self.getExpect(command)
        self.getExpect(self.prompt)
        return self.child.before
    
    def getCommandOutput(self,command):
        """ execute a command against srvrmgr and 
            return the data as a python dictionary
        """
        output = self.execCommand(command)
        data = self.parseOutput(output)
        log.debug("Output for command: '%s' is result:%s" % (command, data))
        return data
    
    def execCommand(self,command):
        """ execute a given srvrmgr command and wait
            for the prompt
        """
        try:
            return self.sendCommand(command)
        except:
            log.warn("no output received from command: '%s'" % command)
            return None
        
    def getExpect(self,match):
        '''check output for connection status'''
        statusDict = {
                      0: {'connect': True, 'msg': 'CONNECTION OK'},
                      1: {'connect': False, 'msg': 'CONNECTION EOF'},
                      2: {'connect': False, 'msg': 'CONNECTION TIMEOUT'},
                      }
        reply = self.child.expect([match,pexpect.EOF,pexpect.TIMEOUT], timeout=self.timeout)
        try:
            self.connected = statusDict[reply]['connect']
            self.message = statusDict[reply]['msg']
        except:
            self.connected = False
            self.message = 'CONNECTION FAILED'
        log.debug("getExpect status for %s: %s , %s" % (match, self.connected, self.message))
    
    def getKeys(self, lines):
        """find keys for output data dict"""
        headline = ''
        for i,line in enumerate(lines):
            # finish query if error detected
            if line.startswith('----'): 
                headline = lines[i-1]
                lines.remove(headline)
                lines.remove(line)
        header = "".join(headline.rstrip('|').split())
        return header.split('|'),lines
    
    def parseOutput(self, output):
        """ convert the srvrmgr output to a python dictionary """
        results = []
        try:
            lines = output.splitlines()
        except:
            lines = []
        keys,lines  =  self.getKeys(lines)
        lines.remove(lines[0]) # this should be the result
        for line in lines:
            if re.match('error code',line) or re.match('system error',line):
                self.status = 1
                return []
            data = dict.fromkeys(keys)
            if '---' in line:  continue
            if len(line) == 0: continue
            if 'rows returned' in line:  continue
            nline =  re.sub("\s\s+",'',line.rstrip('|'))
            values = nline.split('|')
            if len(values) != len(data.keys()) : continue
            for i, v in enumerate(values): 
                data[keys[i]] = v.rstrip(' ').lstrip(' ')
            results.append(data)
        return results
    
    def statDict(self, data=[],keyField=None,valueField=None):
        """ return nagios-style output """
        newDict = {}
        log.debug("statDict keyfield: %s valuefield: %s on data: %s" % (keyField, valueField, data))
        for d in data:
            if keyField in d.keys(): 
                newDict[d[keyField]] = d[valueField]
            #try: newDict[d[keyField]] = d[valueField]
            #except: newDict[d[keyField]] = None
        return newDict
    
    def isServerRunning(self, server):
        """ determine if server is running """
        command = "list server %s show SBLSRVR_STATE" % server
        output = self.getCommandOutput(command)
        try:
            for d in data:
                if data['SBLSRVR_STATE'] == "Running": return True
        except: 
            log.warn("could not determine status of %s using '%s'" % (server, command))
        return False
    
    def testServerConnected(self,server): return self.isServerRunning(server)
    
    def testConnected(self):
        try:
            self.sendCommand('help alias')
        except:
            self.connected = False
            self.message = 'CONNECTION FAILED'
        log.debug('connection test results: %s %s' % (self.connected, self.message))
    
    def testSessionConnected(self):
        """ return True if connected """
        if self.connected == False and self.blocked == True:
            return False
        command = "list servers show SBLSRVR_NAME"
        try:
            if len(self.getCommandOutput(command)) > 0: return True
        except: 
            log.warn("session connection test using '%s' failed" % command)
        return False
    
    def resetConnections(self):
        """"""
        log.debug('refreshing enterprise')
        command = 'refresh enterprise'
        self.child.sendline(command)
        self.testConnected(False)

