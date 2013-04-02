from Products.Zuul.form import schema
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.interfaces import IFacade
from Products.Zuul.utils import ZuulMessageFactory as _t
from Products.ZenModel.ZVersion import VERSION as ZENOSS_VERSION
from Products.ZenUtils.Version import Version

if Version.parse('Zenoss ' + ZENOSS_VERSION) >= Version.parse('Zenoss 4'):
    SingleLineText = schema.TextLine
    MultiLineText = schema.Text
else:
    SingleLineText = schema.Text
    MultiLineText = schema.TextLine


class ISiebelComponentInfo(IComponentInfo):
    ''''''
    CCalias = SingleLineText(title=_t(u'CC Alias'))
    runState = SingleLineText(title=_t(u'State'))
    endTime = SingleLineText(title=_t(u'End Time'))
    CGalias = SingleLineText(title=_t(u'CG Alias'))
    startTime = SingleLineText(title=_t(u'Start Time'))



class IzenSiebelCRMFacade(IFacade):
    ''''''

    def addSiebelComponent(self, ob, **kwargs):
        ''''''


