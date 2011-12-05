"""
SiebelConfigService
ZenHub service for providing configuration to the zensiebelperf collector daemon.
    This provides the daemon with a dictionary of datapoints for every device.
"""

import logging
log = logging.getLogger('zenhub')

from Products.ZenCollector.services.config import CollectorConfigService


class SiebelConfigService(CollectorConfigService):
    """
    ZenHub service for the zensiebelperf collector daemon.
    """
    def __init__(self, dmd, instance):
        deviceProxyAttributes = ('zSiebelGateway',
                                 'zSiebelEnterprise',
                                 'zSiebelServer',
                                 'zSiebelUser',
                                 'zSiebelPassword')
        CollectorConfigService.__init__(self, dmd, instance, deviceProxyAttributes)

    def _filterDevice(self, device):
        filter = CollectorConfigService._filterDevice(self, device)
        if filter:
            try:
                device.siebelComponents()
                filter = True
                log.debug("Device %s included for Siebel collection",device.id)
            except:
                filter = False
            
        return filter

    def _createDeviceProxy(self, device):
        proxy = CollectorConfigService._createDeviceProxy(self, device)
        proxy.configCycleInterval = max(device.zSiebelPerfCycleSeconds, 1)
        proxy.cyclesPerConnection = max(device.zSiebelPerfCyclesPerConnection, 2)
        proxy.timeoutSeconds = max(device.zSiebelPerfTimeoutSeconds, 1)
        
        proxy.datasources = {}
        proxy.datapoints = []
        proxy.thresholds = []

        perfServer = device.getPerformanceServer()

        self._getDataPoints(proxy, device, device.id, None, perfServer)
        proxy.thresholds += device.getThresholdInstances('SiebelPerf')
        proxy.thresholds += device.getThresholdInstances('SiebelTasks')
        proxy.thresholds += device.getThresholdInstances('SiebelStatus')
        
        for component in device.getMonitoredComponents():
            self._getDataPoints(
                proxy, component, component.device().id, component.id,
                perfServer)
            proxy.thresholds += component.getThresholdInstances(
                'Siebel')
        return proxy


    def _getDataPoints(
            self, proxy, deviceOrComponent, deviceId, componentId, perfServer
            ):
        
        for template in deviceOrComponent.getRRDTemplates():
            compId = deviceOrComponent.id
            proxy.datasources[compId] = {}
            
            dataSources = []
            for ds in template.getRRDDataSources():
                if (ds.sourcetype == 'SiebelPerf' or ds.sourcetype == 'SiebelTasks' or ds.sourcetype == 'SiebelStatus'):
                    if ds.enabled:
                        dataSources.append(ds)

            for ds in dataSources:
                dsId = ds.id
                sourcetype = ds.sourcetype
                proxy.datasources[compId][dsId] = {}
                dsInfo = {}
                dsInfo['dsId'] = dsId
                dsInfo['compId'] = compId
                dsInfo['command'] = ds.command.replace('${here/CCalias}',compId)
                dsInfo['sourcetype'] = sourcetype
                dsInfo['dpInfo'] = {}
                for dp in ds.datapoints():
                    dpId = dp.id
                    path = '/'.join((deviceOrComponent.rrdPath(), dp.name()))
                    dpInfo = dict(
                        sourcetype=sourcetype,
                        devId=deviceId,
                        compId=componentId,
                        dpId=dpId,
                        path=path,
                        rrdType=dp.rrdtype,
                        rrdCmd=dp.getRRDCreateCommand(perfServer),
                        minv=dp.rrdmin,
                        maxv=dp.rrdmax,
                        )
                    if componentId:
                        dpInfo['componentDn'] = getattr(
                            deviceOrComponent, 'dn', None)
                    dsInfo[dpId] = dpInfo 
                proxy.datasources[compId][dsId] = dsInfo
                
        log.debug("zensiebelperf found %d datasources",len(proxy.datasources.items()))       

