import os
import json
import paramiko
import io
from typing import List, Dict, Optional

class SSHManager:
    def __init__(self):
        self.servers = self._load_servers()

    def _load_servers(self) -> List[Dict]:
        """Load servers from SERVERS_JSON environment variable."""
        servers_raw = os.getenv('SERVERS_JSON', '[]')
        try:
            return json.loads(servers_raw)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in SERVERS_JSON environment variable.")
            return []

    def get_server_aliases(self) -> List[str]:
        """Return a list of all server aliases for autocomplete."""
        return [s['alias'] for s in self.servers]

    def get_server_by_alias(self, alias: str) -> Optional[Dict]:
        """Find a server configuration by its alias."""
        for s in self.servers:
            if s['alias'] == alias:
                return s
        return None

    def execute_command(self, alias: str, command: str) -> str:
        """Connect to a server by alias and execute a command."""
        config = self.get_server_by_alias(alias)
        if not config:
            return f"Error: Server alias '{alias}' not found."

        # Extract connection details
        host = config.get('host')
        user = config.get('user', 'root')
        port = config.get('port', 22)
        auth_method = config.get('auth_method', 'key')
        secret_env = config.get('secret_env')

        if not secret_env:
            return f"Error: 'secret_env' not defined for server '{alias}'."

        secret_value = os.getenv(secret_env)
        if not secret_value:
            return f"Error: Environment variable '{secret_env}' is empty or not found."

        # Setup SSH Client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if auth_method == 'key':
                # Handle Private Key
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(secret_value))
                client.connect(hostname=host, port=port, username=user, pkey=private_key, timeout=10)
            else:
                # Handle Password
                client.connect(hostname=host, port=port, username=user, password=secret_value, timeout=10)

            # Execute Command
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            client.close()
            return output if output else error

        except Exception as e:
            return f"SSH Error on '{alias}': {str(e)}"
