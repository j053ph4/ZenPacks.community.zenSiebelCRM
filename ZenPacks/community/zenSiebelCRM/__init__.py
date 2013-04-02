import Globals
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenModel.OperatingSystem import OperatingSystem
from Products.ZenUtils.Utils import zenPath,unused
from Definition import *
import os
unused(Globals)

c = Construct(Definition)
c.addDeviceRelation()

# copied from HttpMonitor
def onCollectorInstalled(ob, event):
    zpFriendly = c.componentClass
    errormsg = '{0} binary cannot be found on {1}. This is part of the nagios-plugins ' + \
               'dependency, and must be installed before {2} can function.'
    verifyBin = c.cmdFile
    code, output = ob.executeCommand('zenbincheck %s' % verifyBin, 'zenoss', needsZenHome=True)
    if code:
        log.warn(errormsg.format(verifyBin, ob.hostname, zpFriendly))

class ZenPack(ZenPackBase):
    """ Zenpack install
    """
    packZProperties = c.d.packZProperties
    
    def symlinkScript(self):
        os.system('ln -sf %s/srvrmgr %s/srvrmgr' %
            ('/siebel/siebsrvr/bin', zenPath('libexec')))

    def removeScriptSymlink(self):
        os.system('rm -f %s/srvrmgr' % (zenPath('libexec')))

    def updateRelations(self):
        for d in self.dmd.Devices.getSubDevices():
            d.os.buildRelations()

    def install(self, app):
        c.buildZenPackFiles()
        ZenPackBase.install(self, app)
        self.updateRelations()
        self.symlinkScript()

    def remove(self, app, leaveObjects=False):
        ZenPackBase.remove(self, app, leaveObjects)
        if not leaveObjects:
            OperatingSystem._relations = tuple([x for x in OperatingSystem._relations if x[0] not in (c.relname)])
            self.updateRelations()
        self.removeScriptSymlink()


