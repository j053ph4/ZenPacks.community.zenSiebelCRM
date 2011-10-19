#!/usr/bin/env python
import sys, os, re
import Globals
from optparse import OptionParser
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.ZenUtils.Utils import zenPath,prepId
from ZenPacks.community.zenSiebelCRM.SiebelHandler import SiebelData


class SiebelCollect(ZenScriptBase):
    """ Class to handle input/output from srvrmgr for 
        a Zenoss device
    """
    def __init__(self):
        ZenScriptBase.__init__(self, connect=True)
        self.siebel = SiebelData(self.dmd)

    def buildOptions(self):
        """
        """
        ZenScriptBase.buildOptions(self)
        self.parser.add_option('--server', dest='server',
            help='Remote server')
        self.parser.add_option('--component', dest='component',
            help='Remote Siebel Component')
        self.parser.add_option('--query', dest='query',
            help='One of: runstate, stats, tasks')
        self.parser.add_option('--timeout', dest='timeout',
            help='Command timeout')
    
    def run(self):
        """
        """
        self.siebel.connect(self.options.server,self.options.timeout)
        
        # connect  checks server state.  exit if server not available
        if self.siebel.status != 0:
            self.siebel.disconnect()
            print self.siebel.message
            sys.exit(self.siebel.status)
            
        else:
            if self.options.query == 'runstate': # update component run status
                self.siebel.setComponentStatus(self.options.component)
                
            if self.options.query == 'stats': # collect performance stats
                self.siebel.getStatsForComponent(self.options.component)
                
            if self.options.query == 'tasks': # collect task status
                self.siebel.getTasksForComponent(self.options.component)
    
            self.siebel.disconnect() # close the connection
            
            # print out nagios-style output
            print self.siebel.message
            sys.exit(self.siebel.siebel.status)

if __name__ == "__main__":
    u = SiebelCollect()
    u.run()
