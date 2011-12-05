from Products.Zuul.form import schema
from Products.Zuul.interfaces.component import IComponentInfo
from Products.Zuul.interfaces import IInfo
from Products.Zuul.utils import ZuulMessageFactory as _t


class ISiebelComponentInfo(IComponentInfo):
    CGalias = schema.Text(title=_t(u"CGalias"),group='Overview', order=1)
    runState = schema.Text(title=_t(u"runState"),group='Overview', order=2)
    CCalias = schema.Text(title=_t(u"CCalias"),group='Details')
    startTime = schema.Text(title=_t(u"startTime"),group='Details')
    endTime = schema.Text(title=_t(u"endTime"),group='Details')


class ISiebelPerfDataSourceInfo(IInfo):
    name = schema.Text(title=_t(u"Name"),
                       xtype="idfield",
                       description=_t(u"The name of this datasource"))
    type = schema.Text(title=_t(u"Type"),
                       readonly=True)
    command = schema.Text(title=_t(u"Command"),
                          description=_t(u"Example: list servers show SBLSRVR_NAME,HOST_NAME,SBLSRVR_STATE,START_TIME,END_TIME "))
    enabled = schema.Bool(title=_t(u"Enabled"))

class ISiebelTasksDataSourceInfo(IInfo):
    name = schema.Text(title=_t(u"Name"),
                       xtype="idfield",
                       description=_t(u"The name of this datasource"))
    type = schema.Text(title=_t(u"Type"),
                       readonly=True)
    command = schema.Text(title=_t(u"Command"),
                          description=_t(u"Example: list servers show SBLSRVR_NAME,HOST_NAME,SBLSRVR_STATE,START_TIME,END_TIME "),
                          readonly=True)
    enabled = schema.Bool(title=_t(u"Enabled"))

class ISiebelStatusDataSourceInfo(IInfo):
    name = schema.Text(title=_t(u"Name"),
                       xtype="idfield",
                       description=_t(u"The name of this datasource"))
    type = schema.Text(title=_t(u"Type"),
                       readonly=True)
    command = schema.Text(title=_t(u"Command"),
                          description=_t(u"Example: list servers show SBLSRVR_NAME,HOST_NAME,SBLSRVR_STATE,START_TIME,END_TIME "),
                          readonly=True)
    enabled = schema.Bool(title=_t(u"Enabled"))

