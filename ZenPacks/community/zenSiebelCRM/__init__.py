# Nothing is required in this __init__.py, but it is an excellent place to do
# many things in a ZenPack.
#
# The example below which is commented out by default creates a custom subclass
# of the ZenPack class. This allows you to define custom installation and
# removal routines for your ZenPack. If you don't need this kind of flexibility
# you should leave the section commented out and let the standard ZenPack
# class be used.
#
# Code included in the global scope of this file will be executed at startup
# in any Zope client. This includes Zope itself (the web interface) and zenhub.
# This makes this the perfect place to alter lower-level stock behavior
# through monkey-patching.

import Globals
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import unused
import os

unused(Globals)


class ZenPack(ZenPackBase):
    # All zProperties defined here will automatically be created when the
    # ZenPack is installed.
    packZProperties = [
        ('zSiebelGateway', 'default value', 'string'),
        ('zSiebelEnterprise', 'default value', 'string'),
        ('zSiebelServer', 'default value', 'string'),
        ('zSiebelUser', 'SADMIN', 'string'),
        ('zSiebelPassword', 'sadmin', 'password'),
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

