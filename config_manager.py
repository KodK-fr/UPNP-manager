import json
import os
import logging

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.default_config = {
            'port': 8080,
            'upnp_enabled': False,
            'auto_start': False,
            'theme': 'light',
            'max_file_size': 50,  # Mo
            'allowed_extensions': ['.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico'],
            'last_directory': os.path.expanduser('~'),
            'window_geometry': '1000x700+100+100'
        }

    def load_config(self):
        """Charger la configuration depuis un fichier."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                return {**self.default_config, **config}
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
                return self.default_config.copy()
        return self.default_config.copy()

    def save_config(self, config):
        """Sauvegarder la configuration dans un fichier."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
