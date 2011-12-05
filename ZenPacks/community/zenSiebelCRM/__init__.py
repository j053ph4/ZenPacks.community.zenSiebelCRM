import Globals
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import zenPath,unused
import os

unused(Globals)


class ZenPack(ZenPackBase):
    packZProperties = [
        ('zSiebelGateway', 'default value', 'string'),
        ('zSiebelEnterprise', 'default value', 'string'),
        ('zSiebelServer', 'default value', 'string'),
        ('zSiebelUser', 'SADMIN', 'string'),
        ('zSiebelPassword', 'sadmin', 'password'),
        ('zSiebelPerfCycleSeconds', 300, 'int'),
        ('zSiebelPerfCyclesPerConnection', 5, 'int'),
        ('zSiebelPerfTimeoutSeconds', 10, 'int'),
        ]

    def symlinkScript(self):
        os.system('ln -sf %s/srvrmgr %s/srvrmgr' %
            ('/siebel/siebsrvr/bin', zenPath('libexec')))

    def removeScriptSymlink(self):
        os.system('rm -f %s/srvrmgr' % (zenPath('libexec')))

        
    def install(self, dmd):
        ZenPackBase.install(self, dmd)
         # Put your customer installation logic here.
        self.symlinkScript()
        pass

    def remove(self, dmd, leaveObjects=False):
        if not leaveObjects:
            pass
        self.removeScriptSymlink()
        ZenPackBase.remove(self, dmd, leaveObjects=leaveObjects)

