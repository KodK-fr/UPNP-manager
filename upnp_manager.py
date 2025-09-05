import logging
try:
    import miniupnpc
    UPNP_AVAILABLE = True
except ImportError:
    UPNP_AVAILABLE = False

class UPnPManager:
    def __init__(self):
        self.upnp = None
        self.available = UPNP_AVAILABLE
        if UPNP_AVAILABLE:
            try:
                self.upnp = miniupnpc.UPnP()
                self.upnp.discoverdelay = 200
                self.upnp.discover()
                self.upnp.selectigd()
            except Exception as e:
                logging.error(f"UPnP initialization failed: {e}")
                self.available = False

    def add_port_mapping(self, port):
        """Ajouter une règle de transfert de port UPnP."""
        if not self.available or not self.upnp:
            return False
        try:
            result = self.upnp.addportmapping(port, 'TCP', self.upnp.lanaddr, port, 'Port Forwarding App', '')
            logging.info(f"Port mapping added for port {port}")
            return result
        except Exception as e:
            logging.error(f"Failed to add port mapping: {e}")
            return False

    def delete_port_mapping(self, port):
        """Supprimer une règle de transfert de port UPnP."""
        if not self.available or not self.upnp:
            return False
        try:
            result = self.upnp.deleteportmapping(port, 'TCP')
            logging.info(f"Port mapping deleted for port {port}")
            return result
        except Exception as e:
            logging.error(f"Failed to delete port mapping: {e}")
            return False

    def get_public_ip(self):
        """Obtenir l'adresse IP publique."""
        if not self.available or not self.upnp:
            return None
        try:
            return self.upnp.externalipaddress()
        except Exception as e:
            logging.error(f"Failed to get public IP: {e}")
            return None

    def list_port_mappings(self):
        """Lister les règles de transfert de port UPnP."""
        if not self.available or not self.upnp:
            return []
        mappings = []
        try:
            i = 0
            while True:
                p = self.upnp.getgenericportmapping(i)
                if p is None:
                    break
                mappings.append({
                    'external_port': p[0],
                    'protocol': p[1],
                    'internal_ip': p[2],
                    'internal_port': p[3],
                    'description': p[4]
                })
                i += 1
        except Exception as e:
            logging.error(f"Failed to list port mappings: {e}")
        return mappings
