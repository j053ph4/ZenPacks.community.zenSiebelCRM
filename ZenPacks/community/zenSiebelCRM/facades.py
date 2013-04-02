import os,re
import logging
log = logging.getLogger('zen.zenSiebelCRMFacade')

from zope.interface import implements
from Products.Zuul.facades import ZuulFacade
from Products.Zuul.utils import ZuulMessageFactory as _t
from SiebelComponent import *
from .interfaces import *

class zenSiebelCRMFacade(ZuulFacade):
    implements(IzenSiebelCRMFacade)
 

    def addSiebelComponent(self, ob, **kwargs):
    	target = ob
    
        from Products.ZenUtils.Utils import prepId
        from ZenPacks.community.zenSiebelCRM.SiebelComponent import SiebelComponent
        import re
        cid = 'siebelcomponent' 
        for k,v in kwargs.iteritems():
            if type(v) != bool:
                cid += str(v)
        cid = re.sub('[^A-Za-z0-9]+', '_', cid)
        id = prepId(cid)
        component = SiebelComponent(id)
        relation = target.os.siebelComponents
        relation._setObject(component.id, component)
        component = relation._getOb(component.id)
        for k,v in kwargs.iteritems():
            setattr(component,k,v) 
        
    
    
    

    	return True, _t("Added Siebel Component for device " + target.id)

