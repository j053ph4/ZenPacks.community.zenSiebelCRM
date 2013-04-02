##########################################################################
#
#   Copyright 2009 Zenoss, Inc. All Rights Reserved.
#
##########################################################################

from SiebelHandler import SiebelHandler, SiebelData
#from pysamba.rpc.Rpc import Rpc
#from pysamba.talloc import talloc_zero, talloc_array, talloc_free
#from pysamba.composite_context import composite_context
from twisted.internet import defer
from ctypes import *

import Globals
from Products.ZenUtils.Driver import drive

import datetime
import logging

#from winreg import *
#from pysamba.library import library

#library.dcerpc_winreg_OpenHKPD_send.restype = c_void_p
#library.dcerpc_winreg_OpenHKPD_send.argtypes = [c_void_p, c_void_p, c_void_p]
#library.dcerpc_winreg_QueryValue_send.restype = c_void_p
#library.dcerpc_winreg_QueryValue_send.argtypes = [c_void_p, c_void_p, c_void_p]
#library.dcerpc_winreg_CloseKey_send.restype = c_void_p
#library.dcerpc_winreg_CloseKey_send.argtypes = [c_void_p, c_void_p, c_void_p]

def commands(obj):
    "Compute a typed pointer to an object"
    return cast(addressof(obj), POINTER(obj.__class__))

class FetchBeforeConnectedError(Exception): pass

class PerfSrvrmgr(SiebelHandler):
    def __init__(self, commands, capturePath=None):
        SiebelHandler.__init__(self)
        self.siebel = SiebelHandler()
        self.log = logging.getLogger("zen.siebelperf.PerfSrvrmgr")
        self.logLevel = log.getEffectiveLevel()
        self.commands = commands
        self.handle = None
        self.prev = None
        self.connected = False
        self.capturePath = capturePath
        self.fetches = 0
        self.ownerDevice = None

#    def set_name(self, query):
#        "Sent the query name in a QueryValue request"
#        p = self.params.contents
#        p._in.value_name.name = query
#        p._in.value_name.name_len = 2 * library.strlen_m_term(query)
#        p._in.value_name.name_size = p._in.value_name.name_len

    def connect(self, host, credentials):
        log.info("__finishDel")
        pass
        self.host = host
        #def inner(driver):
        #yield Rpc.connect(self, host, credentials, 'winreg')
        #    yield self.siebel.initialize(credentials,timeout=120)
        #    driver.next()

        #params = talloc_zero(self.ctx, winreg_OpenHKPD)
        #self.handle = talloc_zero(self.ctx, policy_handle)
        #params.contents.out.handle = self.handle
        #yield self.call(library.dcerpc_winreg_OpenHKPD_send, params)
        #self.hkpt = driver.next()

        # first learn how big the data is
        #if self.logLevel <= logging.DEBUG:
        #    self.log.debug("Learning command object ids")
        #self.type = enum()
        #self.size = uint32_t()
#        self.out_size = uint32_t()
#        self.length = uint32_t()
#        self.type.value = self.size.value = self.length.value = 0
#        self.params = talloc_zero(self.ctx, winreg_QueryValue)
#        p = self.params.contents
#        p._in.handle = self.handle
#        self.set_name('Commands')
#        p._in.type = p.out.type = pointerTo(self.type)
#        p._in.size = pointerTo(self.size)
#        p.out.size = pointerTo(self.out_size)
#        p.out.length = p._in.length = pointerTo(self.length)
#        p._in.data = p.out.data = None
#        yield self.call(library.dcerpc_winreg_QueryValue_send, self.params)
#        driver.next()

#        # allocate space
#        sz = p.out.size.contents.value
#        if self.logLevel <= logging.DEBUG:
#            self.log.debug("size is %d", sz)
#        p.out.data = p._in.data = talloc_array(params, uint8_t, sz)
#        self.size.value = sz
#        self.length.value = 0 # we don't need to xmit any raw data
#        # now fetch it
#        yield self.call(library.dcerpc_winreg_QueryValue_send, self.params)
#        driver.next()

#        # now decode the mapping of commands to indexes
#        REG_MULTI_SZ = 7
#        data = string_at(p.out.data, p.out.length.contents.value)
#        assert p.out.type.contents.value == REG_MULTI_SZ
#
#        # save the counter data if requested to do so
#        if self.capturePath:
#            capFile = open("%s-%s-commands" % (self.capturePath, self.host), "w")
#            capFile.write(data)
#            capFile.close()

        # it's a null-separated list of number/name pairs
#        def pairs(seq):
#            i = iter(seq)
#            while 1:
#                yield (i.next(), i.next())
#        self.counterMap = {}
#        self.counterRevMap = {}
#        for index, name in pairs(data.decode('utf-16').split(u'\x00')):
#            if self.logLevel < logging.DEBUG:
#                self.log.log(logging.DEBUG-1, "Found counter: %r=%r", index, name)
#            if index:
#                key = name.decode('latin-1').lower()
#                try:
#                    value = int(index)
#                except ValueError, e:
#                    self.log.warn("Found non-numeric counter: %s=%s",
#                        index, name)
#                else:
#                    self.counterMap[key] = value
#                    self.counterRevMap[value] = key
#
#        objects = set()
#        for path in self.commands:
#            try:
#                object, _, _, _, _ = parseCounter(path)
#                objects.add(object.lower())
#            except AttributeError:
#                self.log.error("The counter name %s is invalid -- ignoring.", path)
#
#        ids = []
#        for obj in objects:
#            if self.counterMap.has_key(obj):
#                ids.append(self.counterMap[obj])
#                if self.logLevel <= logging.DEBUG:
#                    self.log.debug("Found Perfmon Object: %r=%r", self.counterMap[obj], obj)
#        ids.sort()
#        query = ' '.join(map(str, ids))
#        if self.logLevel <= logging.DEBUG:
#            self.log.debug("Perfmon Object query: %s", query)
        #self.set_name(query)
        #self.connected = True
#      return drive(inner)
#
#    def fetch(self):
##      p = self.params.contents
##      if not self.connected:
##          raise FetchBeforeConnectedError()
#      def inner(driver):
##        ctx = talloc_zero(self.ctx, composite_context)
#        try:
#            # If hKey specifies HKEY_PERFORMANCE_DATA and the lpData buffer
#            # is not large enough to contain all of the returned data,
#            # RegQueryValueEx returns ERROR_MORE_DATA and the value returned
#            # through the lpcbData parameter is undefined. This is because
#            # the size of the performance data can change from one call to
#            # the next. In this case, you must increase the buffer size and
#            # call RegQueryValueEx again passing the updated buffer size in
#            # the lpcbData parameter. Repeat this until the function
#            # succeeds. You need to maintain a separate variable to keep
#            # track of the buffer size, because the value returned by
#            # lpcbData is unpredictable.
#            while 1:
#              if self.logLevel <= logging.DEBUG:
#                self.log.debug("Fetching commands")
#              self.length.value = 0 # we don't need to xmit any raw data
#              yield self.call(library.dcerpc_winreg_QueryValue_send,
#                              self.params,
#                              ctx)
#              driver.next()
#
#              if p.out.result.v == 234L: # ERROR_MORE_DATA
#                sz = self.size.value + 65536
#                if self.logLevel <= logging.DEBUG:
#                  self.log.debug("ERROR_MORE_DATA returned, increasing buffer size to %d", sz)
#                p.out.data = p._in.data = talloc_array(self.params, uint8_t, sz)
#                self.size.value = sz
#                continue
#
#              break
#
#            data = string_at(p.out.data, p.out.length.contents.value)
#            if self.logLevel <= logging.DEBUG:
#                self.log.debug("Counter data fetched, length=%d",
#                               p.out.length.contents.value)
#
#            # save the raw data if requested to do so
#            if self.capturePath:
#                capFile = open("%s-%s-%d" % (self.capturePath, self.host, self.fetches), "w")
#                capFile.write(data)
#                capFile.close()
#                self.fetches = self.fetches + 1
#
#            perf = PerformanceData(data, self.counterRevMap)
#            result = {}
#            for path in self.commands:
#                try:
#                    result[path] = getCounterValue(path, perf, self.prev)
#                except (AttributeError, KeyError):
#                    summaryMsg = "Bad counter for device %s: %s" % (self.host, path)
#                    self.log.warning(summaryMsg)
#                    if self.ownerDevice is not None:
#                        self.ownerDevice._eventService.sendEvent(
#                                             self.ownerDevice.WARNING_EVENT,
#                                             component = "zen.winperf.PerfRpc",
#                                             device = self.ownerDevice._devId,
#                                             summary = summaryMsg)
#
#            self.prev = perf
#            talloc_free(ctx)
#            ctx = None
#            yield defer.succeed(result)
#            driver.next()
#        except Exception, ex:
#            if ctx is not None:
#                talloc_free(ctx)
#                ctx = None
#            raise
#
#      # don't bother fetching any data if there are no commands to fetch
#      if p._in.value_name.name:
#          d = drive(inner)
#      else:
#          d = defer.fail("No PerfMon objects to query")
#      return d

    def __finishDel(self, result):
        log.info("__finishDel")
        pass
        #super(PerfRpc, self).__del__()

    def __del__(self):
        log.info("__del__")
        pass
        #d = self.stop()
        #d.addBoth(self.__finishDel)
        #return d

    def _stopFinished(self, result):
        log.info("_stopFinished")
        pass
        #talloc_free(self.handle)
        #self.handle = None
        #self.close()
        #self.ownerDevice = None
        #return result

    def stop(self):
        log.info("stop")
        pass
        #if self.handle is None:
        #    d = defer.succeed(None)
        #else:
            #params = talloc_zero(self.handle, winreg_CloseKey)
            #params.contents._in.handle = self.handle
            #params.contents.out.handle = self.handle
            #d = self.call(library.dcerpc_winreg_CloseKey_send, params)
            #d.addBoth(self._stopFinished)
        #return d

