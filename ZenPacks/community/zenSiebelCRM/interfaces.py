from Products.Zuul.form import schema
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.utils import ZuulMessageFactory as _t


class ISiebelComponentInfo(IComponentInfo):
    CGalias = schema.Text(title=_t(u"CGalias"),group='Overview', order=1)
    runState = schema.Text(title=_t(u"runState"),group='Overview', order=2)
    CCalias = schema.Text(title=_t(u"CCalias"),group='Details')
    startTime = schema.Text(title=_t(u"startTime"),group='Details')
    endTime = schema.Text(title=_t(u"endTime"),group='Details')

