#!/usr/bin/env python
"""OSX-based script to watch for changes to network state and write out a second
resolv.conf file containing the DHCP provided nameservers, intended for use with
a local resolver such as dnsmasq. This is to workaround the changes in Snow Leopard
from Leopard with regards to DNS resolution -- ie: the inability to have both manually
configured nameservers and DHCP provided ones as well as the issues with split-DNS.

usage: python automasq.py /path/to/second/resolv.conf

"""
import sys

from SystemConfiguration import *

GLOBAL_KEY = 'State:/Network/Global/IPv4'

class Watcher(object):
    def __init__(self, filename):
        self.filename = filename

        store = self.store = SCDynamicStoreCreate(None, "automasq", self.dynamicStoreChanged, None)
        SCDynamicStoreSetNotificationKeys(store, None, [GLOBAL_KEY])
        source = self.source = SCDynamicStoreCreateRunLoopSource(None, store, 0)

        self.write_file(self.get_primary_dns(store))

        loop = self.loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(loop, source, kCFRunLoopCommonModes)
        CFRunLoopRun()

    def write_file(self, servers=[]):
        with open(self.filename, 'w+') as f:
            for server in servers:
                f.write('nameserver %s\n' % server)

    def process_dns_for_service(self, store, service):
        key = 'State:/Network/Service/%s/DNS' % service
        val = SCDynamicStoreCopyValue(store, key)  
        data = list(dict(val)['ServerAddresses'])
        return data

    def get_primary_dns(self, store=None):
        store = store or self.store
        val = SCDynamicStoreCopyValue(store, GLOBAL_KEY)
        if val:
            data = dict(val)
            svcid = data['PrimaryService']
            return self.process_dns_for_service(store, svcid)
        else:
            return []

    def dynamicStoreChanged(self, store, changedKeys, info):
        servers = []
        for key in list(changedKeys):
            #if key == GLOBAL_KEY:
            servers = self.get_primary_dns(store)
            self.write_file(servers)


def dummy_timer(*args):
    pass


def main(filename):
    # this gives us a callback into python every 1s for signal handling
    CFRunLoopAddTimer(CFRunLoopGetCurrent(),
        CFRunLoopTimerCreate(None, CFAbsoluteTimeGetCurrent(), 1.0, 0, 0, dummy_timer, None),
        kCFRunLoopCommonModes)
    try:
        watcher = Watcher(filename)
    except KeyboardInterrupt, e:
        # exiting
        pass

if __name__ == '__main__':
    main(sys.argv[1])

