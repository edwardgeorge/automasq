import signal
import sys

from SystemConfiguration import *

GLOBAL_KEY = 'State:/Network/Global/IPv4'

def sigint(*args):
    print "SIGINT: bailing out"
    loop = CFRunLoopGetCurrent()
    CFRunLoopStop(loop)

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

def main(filename):
    signal.signal(signal.SIGINT, sigint)
    watcher = Watcher(filename)

if __name__ == '__main__':
    main(sys.argv[1])
