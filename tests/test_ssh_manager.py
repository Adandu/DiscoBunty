import unittest
from ssh_manager import SSHManager

class TestSSHManager(unittest.TestCase):
    def setUp(self):
        self.servers = [
            {"alias": "server1", "ip": "1.1.1.1"},
            {"alias": "server2", "ip": "2.2.2.2"},
            {"alias": "web-prod", "ip": "3.3.3.3"},
        ]
        self.manager = SSHManager(self.servers)

    def test_get_server_aliases_returns_all_aliases(self):
        """Test that get_server_aliases returns a list of all defined aliases."""
        aliases = self.manager.get_server_aliases()
        self.assertEqual(aliases, ["server1", "server2", "web-prod"])

    def test_get_server_aliases_empty(self):
        """Test that get_server_aliases returns an empty list when initialized with no servers."""
        manager = SSHManager([])
        self.assertEqual(manager.get_server_aliases(), [])

    def test_get_server_aliases_none_values(self):
        """Test that get_server_aliases handles alias values that might be None."""
        servers = [
            {"alias": None, "ip": "1.1.1.1"},
            {"alias": "valid_alias", "ip": "2.2.2.2"}
        ]
        manager = SSHManager(servers)
        aliases = manager.get_server_aliases()
        self.assertEqual(aliases, [None, "valid_alias"])

if __name__ == "__main__":
    unittest.main()
