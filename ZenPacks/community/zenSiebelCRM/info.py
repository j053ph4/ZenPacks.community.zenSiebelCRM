from zope.component import adapts
from zope.interface import implements
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.infos import InfoBase
from ZenPacks.community.zenSiebelCRM.SiebelComponent import SiebelComponent
from ZenPacks.community.zenSiebelCRM.interfaces import *


class SiebelComponentInfo(ComponentInfo):
    implements(ISiebelComponentInfo)
    adapts(SiebelComponent)
    CGalias = ProxyProperty("CGalias")
    CCalias = ProxyProperty("CCalias")
    runState = ProxyProperty("runState")
    startTime = ProxyProperty("startTime")
    endTime = ProxyProperty("endTime")

class SiebelPerfDataSourceInfo(InfoBase):
    implements(ISiebelPerfDataSourceInfo)

    @property
    def id(self):
        return '/'.join( self._object.getPrimaryPath() )

    @property
    def source(self):
        return self._object.getDescription()

    @property
    def type(self):
        return self._object.sourcetype

    command = ProxyProperty('command')
    enabled = ProxyProperty('enabled')

    @property
    def testable(self):
        """
        We can test this datasource against a specific siebel device
        """
        return True

class SiebelTasksDataSourceInfo(InfoBase):
    implements(ISiebelTasksDataSourceInfo)

    @property
    def id(self):
        return '/'.join( self._object.getPrimaryPath() )

    @property
    def source(self):
        return self._object.getDescription()

    @property
    def type(self):
        return self._object.sourcetype

    command = ProxyProperty('command')
    enabled = ProxyProperty('enabled')

    @property
    def testable(self):
        """
        We can test this datasource against a specific siebel device
        """
        return True
    
class SiebelStatusDataSourceInfo(InfoBase):
    implements(ISiebelStatusDataSourceInfo)

    @property
    def id(self):
        return '/'.join( self._object.getPrimaryPath() )

    @property
    def source(self):
        return self._object.getDescription()

    @property
    def type(self):
        return self._object.sourcetype

    command = ProxyProperty('command')
    enabled = ProxyProperty('enabled')

    @property
    def testable(self):
        """
        We can test this datasource against a specific siebel device
        """
        return True

