"""
SiebelConfigService
ZenHub service for providing configuration to the zensiebelperf collector daemon.
    This provides the daemon with a dictionary of datapoints for every device.
"""
import logging
log = logging.getLogger('zen.zensiebelperf')

from Products.ZenCollector.services.config import CollectorConfigService
from ZenPacks.community.zenSiebelCRM.Definition import *

class SiebelConfigService(CollectorConfigService):
    """
    ZenHub service for the zensiebelperf collector daemon.
    """
    def __init__(self, dmd, instance):
        # attributes that will be available to the daemon
        self.definition = SiebelDefinition
        deviceProxyAttributes = tuple([p[0] for p in self.definition.packZProperties])                         
        CollectorConfigService.__init__(self, dmd, instance, deviceProxyAttributes)
        srvrmgrs = []

    def _filterDevice(self, device):
        ''''''
        log.debug("filtering for %s" % device.id)
        filter = CollectorConfigService._filterDevice(self, device)
        if filter:
            if len(device.os.siebelComponents()) > 0:
                log.debug("Device %s included for Siebel collection",device.id)
                return True
            else:
                return False
        return False

    def _createDeviceProxy(self, device):
        ''''''
        log.debug('getting proxy for device %s' % device.id)
        proxy = CollectorConfigService._createDeviceProxy(self, device)
        proxy.configCycleInterval = max(device.zSiebelPerfCycleSeconds,300)
        proxy.cyclesPerConnection = max(device.zSiebelPerfCyclesPerConnection, 288)
        proxy.timeoutSeconds = max(device.zSiebelPerfTimeoutSeconds, 30)
        #proxy.shareGateway = device.zSiebelShareGateway
        
        proxy.datasources = {}
        proxy.dpInfo = []
        proxy.datapoints = []
        proxy.thresholds = []
        perfServer = device.getPerformanceServer()
        log.debug("device %s has perfServer %s" % (device.id, perfServer) )
        self._getDataPoints(proxy, device, device.id, None, perfServer)
        proxy.thresholds += device.getThresholdInstances(self.definition.component)

        for component in device.getMonitoredComponents():
            self._getDataPoints(proxy, component, component.device().id, component.id, perfServer)
            proxy.thresholds += component.getThresholdInstances(self.definition.component)
        return proxy

    def _getDataPoints(self, proxy, deviceOrComponent, deviceId, componentId, perfServer):
        ''''''
        for template in deviceOrComponent.getRRDTemplates():
            compId = deviceOrComponent.id
            dstypes = [SiebelDefinition.component]
            dataSources = []
            for ds in template.getRRDDataSources(self.definition.component):
                if ds.enabled:
                    proxy.datasources[compId] = {}
                    dataSources.append(ds)
                    log.debug("Adding datasource %s for component: %s on device: %s",ds.id,compId,deviceId)

            for ds in dataSources:
                dsId = ds.id
                sourcetype = ds.sourcetype
                proxy.datasources[compId][dsId] = {}
                dsInfo = {}
                dsInfo['dsId'] = dsId
                dsInfo['compId'] = compId
                dsInfo['command'] = ds.getCommand(deviceOrComponent)
                log.debug("got command: %s" % dsInfo['command'])
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
                
        log.debug("SiebelConfigService found %d datasources",len(proxy.datasources.items()))       

