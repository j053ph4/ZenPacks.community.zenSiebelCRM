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
        self.parser.add_option('--timeout', dest='timeout',
            help='Command timeout')
    
    def run(self):
        """
        """
        self.siebel.connect(self.options.server,int(float(self.options.timeout)))
        self.siebel.updateStatus()
        # connect  checks server state.  exit if server not available
        if self.siebel.checkQuery() == False:
            self.siebel.message = 'WARNING: Query failed on '+self.options.server
        else:
            self.siebel.message = 'OK: Query successful on '+self.options.server
            self.siebel.getStatsForComponent(self.options.component) # collect performance stats
            self.siebel.getTasksForComponent(self.options.component) # collect task status
            self.siebel.getComponentRunStatus(self.options.component) # update component run status

        self.siebel.disconnect()
        print self.siebel.message
        sys.exit(self.siebel.status)
            
if __name__ == "__main__":
    u = SiebelCollect()
    u.run()
