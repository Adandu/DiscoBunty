import os
import json
import logging
import copy
from crypto_utils import CryptoManager

logger = logging.getLogger('discobunty.config')

DEFAULT_CONFIG = {
    "discord": {
        "token": "",
        "guild_id": "",
        "allowed_roles": "Admin,DevOps"
    },
    "features": {
        "enable_docker": "false",
        "power_control_enabled": "false",
        "power_control_password": ""
    },
    "webui": {
        "enabled": "true",
        "password": ""
    },
    "servers": []
}

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        # SECRET_KEY must still come from environment for initial decryption
        secret_key = os.getenv('SECRET_KEY')
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable is mandatory.")
            
        self.crypto = CryptoManager(secret_key)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_path}")
                    return self._process_config(config, decrypt=True)
            except Exception as e:
                logger.error(f"Failed to load config.json: {e}")
        
        logger.warning("Config file not found or invalid. Using defaults/env migration.")
        return self._migrate_from_env()

    def _migrate_from_env(self) -> dict:
        """Helper to migrate existing .env settings to the new JSON format."""
        # Use deepcopy to avoid mutating the global DEFAULT_CONFIG
        config = copy.deepcopy(DEFAULT_CONFIG)
        
        # Mapping from .env keys to JSON structure
        config["discord"]["token"] = os.getenv('DISCORD_TOKEN', '')
        config["discord"]["guild_id"] = os.getenv('GUILD_ID', '')
        config["discord"]["allowed_roles"] = os.getenv('ALLOWED_ROLES', '')
        
        config["features"]["enable_docker"] = os.getenv('ENABLE_DOCKER', 'false').lower()
        config["features"]["power_control_enabled"] = os.getenv('POWER_CONTROL_ENABLED', 'false').lower()
        config["features"]["power_control_password"] = os.getenv('POWER_CONTROL_PASSWORD', '')
        
        config["webui"]["enabled"] = os.getenv('WEBUI_ENABLED', 'true').lower()
        config["webui"]["password"] = os.getenv('WEB_PASSWORD', '')
        
        # Servers migration
        i = 1
        while True:
            alias = os.getenv(f'DISCORD_UBUNTU_SERVER_ALIAS_{i}')
            if not alias: break
            
            server = {
                "alias": alias,
                "host": os.getenv(f'DISCORD_UBUNTU_SERVER_IP_{i}'),
                "user": os.getenv(f'DISCORD_UBUNTU_SERVER_USER_{i}', 'root'),
                "port": int(os.getenv(f'DISCORD_UBUNTU_SERVER_PORT_{i}', '22')),
                "auth_method": os.getenv(f'DISCORD_UBUNTU_SERVER_AUTH_METHOD_{i}', 'key').lower(),
                "password": os.getenv(f'DISCORD_UBUNTU_SERVER_PASSWORD_{i}', ''),
                "key": os.getenv(f'DISCORD_UBUNTU_SERVER_KEY_{i}', '')
            }
            config["servers"].append(server)
            i += 1
            
        # Save the migrated config (will encrypt automatically in save_config)
        self.config = config
        self.save_config(config)
        return config

    def _process_config(self, config: dict, decrypt: bool = True) -> dict:
        """Recursively encrypt or decrypt passwords in the config."""
        # Process Discord Token (Critical fix: Discord token is now encrypted)
        if "discord" in config and config["discord"].get("token"):
            t = config["discord"]["token"]
            config["discord"]["token"] = self.crypto.decrypt(t) if decrypt else self.crypto.encrypt(t)

        # Process top-level passwords
        if "features" in config and config["features"].get("power_control_password"):
            p = config["features"]["power_control_password"]
            config["features"]["power_control_password"] = self.crypto.decrypt(p) if decrypt else self.crypto.encrypt(p)
            
        if "webui" in config and config["webui"].get("password"):
            p = config["webui"]["password"]
            config["webui"]["password"] = self.crypto.decrypt(p) if decrypt else self.crypto.encrypt(p)

        # Process server passwords/keys
        if "servers" in config:
            for s in config["servers"]:
                if s.get("password"):
                    s["password"] = self.crypto.decrypt(s["password"]) if decrypt else self.crypto.encrypt(s["password"])
                if s.get("key"):
                    # Only encrypt/decrypt if it's not a path
                    if s["key"] and not (s["key"].startswith('/') or os.path.isfile(s["key"])):
                        s["key"] = self.crypto.decrypt(s["key"]) if decrypt else self.crypto.encrypt(s["key"])
        
        return config

    def save_config(self, new_config: dict):
        """Save configuration to JSON file with encryption."""
        # Deep copy to avoid encrypting the in-memory config
        to_save = copy.deepcopy(new_config)
        to_save = self._process_config(to_save, decrypt=False)
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(to_save, f, indent=4)
            self.config = new_config # Update in-memory config
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save {self.config_path}: {e}")

    def get_server_config(self) -> list:
        return self.config.get("servers", [])
