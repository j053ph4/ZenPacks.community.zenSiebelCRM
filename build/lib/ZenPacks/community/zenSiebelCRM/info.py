from zope.interface import implements
from Products.Zuul.infos import ProxyProperty
from Products.Zuul.infos.component import ComponentInfo
from ZenPacks.community.zenSiebelCRM.interfaces import *

'''
args:  zenpack,compInfo,compInterface,infoProperties
'''

class SiebelComponentInfo(ComponentInfo):
    implements( ISiebelComponentInfo )
    CCalias = ProxyProperty('CCalias')
    runState = ProxyProperty('runState')
    endTime = ProxyProperty('endTime')
    CGalias = ProxyProperty('CGalias')
    startTime = ProxyProperty('startTime')


