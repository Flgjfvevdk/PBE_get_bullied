from pathlib import Path
from typing import Optional, Set

DEFAULT_LANG = "en"

class LanguageManager:
    def __init__(self, config_dir: str = "config"):
        """Initialize the language manager with configuration directory."""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.fr_servers: Set[str] = set()
        self.en_servers: Set[str] = set()
        
        self._load_configs()
    
    def _load_configs(self):
        """Load server configurations from text files."""
        fr_file = self.config_dir / "servers_fr.txt"
        if fr_file.exists():
            try:
                with open(fr_file, 'r', encoding='utf-8') as f:
                    self.fr_servers = {line.strip() for line in f if line.strip()}
            except IOError:
                pass

        en_file = self.config_dir / "servers_en.txt"
        if en_file.exists():
            try:
                with open(en_file, 'r', encoding='utf-8') as f:
                    self.en_servers = {line.strip() for line in f if line.strip()}
            except IOError:
                pass
    
    def _save_config(self, lang: str, servers: Set[str]):
        """Save server configuration to text file."""
        filepath = self.config_dir / f"servers_{lang}.txt"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for server_id in sorted(servers):
                    f.write(f"{server_id}\n")
        except IOError:
            pass
    
    def get_server_language(self, guild_id: Optional[int]) -> str:
        """
        Get the language for a server.
        
        Args:
            guild_id: Discord server ID, None for DMs
            
        Returns:
            Language code ('fr' or 'en')
        """
        if guild_id is None:
            return DEFAULT_LANG
        
        guild_id_str = str(guild_id)
        
        if guild_id_str in self.fr_servers:
            return "fr"
        elif guild_id_str in self.en_servers:
            return "en"
        else:
            return DEFAULT_LANG
    
    def set_server_language(self, guild_id: int, lang: str) -> bool:
        """
        Set the language for a server.
        
        Args:
            guild_id: Discord server ID
            lang: Language code ('fr' or 'en')
            
        Returns:
            True if successful, False otherwise
        """
        if lang not in ["fr", "en"]:
            return False
        
        guild_id_str = str(guild_id)
        
        self.fr_servers.discard(guild_id_str)
        self.en_servers.discard(guild_id_str)
        
        if lang == "fr":
            self.fr_servers.add(guild_id_str)
        else:
            self.en_servers.add(guild_id_str)
        
        self._save_config("fr", self.fr_servers)
        self._save_config("en", self.en_servers)
        
        return True
    
    def reload_configs(self):
        """Reload configurations from files."""
        self._load_configs()

language_manager_instance = LanguageManager()