import unittest


class TestLanguageSubtagRegistry(unittest.TestCase):
    
    def setUp(self) -> None:
        global Registry
        from musculus.metadata.langtag.registry import Registry

    def test_registry(self):
        reg = Registry.load_file()
        