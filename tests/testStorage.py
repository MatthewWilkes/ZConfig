import os
import tempfile
import unittest
from StringIO import StringIO

import ZConfig
from ZConfig import Storage

class StorageTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.tmpfn = tempfile.mktemp()
        self.storage = None

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        storage = self.storage
        self.storage = None
        try:
            if storage is not None:
                storage.close()
        except:
            pass
        try:
            os.remove(self.tmpfn)
        except os.error:
            pass

    def testFileStorage(self):
        from ZODB.FileStorage import FileStorage
        sample = """
        <Storage>
        type       FileStorage
        file_name  %s
        create     1
        </Storage>
        """ % self.tmpfn
        io = StringIO(sample)
        rootconf = ZConfig.loadfile(io)
        storageconf = rootconf.getSection("Storage")
        cls, args = Storage.getStorageInfo(storageconf)
        self.assertEqual(cls, FileStorage)
        self.assertEqual(args, {"file_name": self.tmpfn, "create": 1})
        self.storage = Storage.createStorage(storageconf)
        self.assert_(isinstance(self.storage, FileStorage))

    def testZEOStorage(self):
        from ZEO.ClientStorage import ClientStorage
        sample = """
        <Storage>
        type       ClientStorage
        addr       %s
        wait       0
        </Storage>
        """ % self.tmpfn
        io = StringIO(sample)
        rootconf = ZConfig.loadfile(io)
        storageconf = rootconf.getSection("Storage")
        cls, args = Storage.getStorageInfo(storageconf)
        self.assertEqual(cls, ClientStorage)
        self.assertEqual(args, {"addr": [self.tmpfn], "wait": 0})
        self.storage = Storage.createStorage(storageconf)
        self.assert_(isinstance(self.storage, ClientStorage))

    def testDemoStorage(self):
        from ZODB.DemoStorage import DemoStorage
        sample = """
        <Storage>
        type       DemoStorage
        </Storage>
        """
        io = StringIO(sample)
        rootconf = ZConfig.loadfile(io)
        storageconf = rootconf.getSection("Storage")
        cls, args = Storage.getStorageInfo(storageconf)
        self.assertEqual(cls, DemoStorage)
        self.assertEqual(args, {})
        self.storage = Storage.createStorage(storageconf)
        self.assert_(isinstance(self.storage, DemoStorage))

    def testModuleStorage(self):
        # Test explicit module+class
        from ZODB.DemoStorage import DemoStorage
        sample = """
        <Storage>
        type       ZODB.DemoStorage.DemoStorage
        </Storage>
        """
        io = StringIO(sample)
        rootconf = ZConfig.loadfile(io)
        storageconf = rootconf.getSection("Storage")
        cls, args = Storage.getStorageInfo(storageconf)
        self.assertEqual(cls, DemoStorage)
        self.assertEqual(args, {})
        self.storage = Storage.createStorage(storageconf)
        self.assert_(isinstance(self.storage, DemoStorage))

def test_suite():
    return unittest.makeSuite(StorageTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
