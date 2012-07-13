import Globals
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import zenPath,unused
import os

unused(Globals)


class ZenPack(ZenPackBase):
    packZProperties = [
        ('zSiebelGateway', 'GATEWAY', 'string'),
        ('zSiebelEnterprise', 'ENTERPRISE', 'string'),
        ('zSiebelServer', 'SERVER', 'string'),
        ('zSiebelUser', 'USER', 'string'),
        ('zSiebelPassword', 'PASSWORD', 'password'),
        ('zSiebelPerfCycleSeconds', 300, 'int'),
        ('zSiebelPerfCyclesPerConnection', 288, 'int'),
        ('zSiebelPerfTimeoutSeconds', 10, 'int'),
        ('zSiebelShareGateway',True,'boolean')
        ]

    def symlinkScript(self):
        os.system('ln -sf %s/srvrmgr %s/srvrmgr' %
            ('/siebel/siebsrvr/bin', zenPath('libexec')))

    def removeScriptSymlink(self):
        os.system('rm -f %s/srvrmgr' % (zenPath('libexec')))

    def install(self, app):
        ZenPackBase.install(self, app)
         # Put your customer installation logic here.
        self.symlinkScript()
        pass

    def remove(self, app, leaveObjects=False):
        if not leaveObjects:
            pass
        self.removeScriptSymlink()
        ZenPackBase.remove(self, app, leaveObjects)

