from typing import Optional
from discord.ext.commands import Context
from utils.language_manager import language_manager_instance

def getTuto(tuto_name: str, ctx: Optional[Context] = None, lang: Optional[str] = None):
    """
    Returns the tutorial text for the given tutorial name in the specified language.
    
    Args:
        tuto_name: Name of the tutorial
        ctx: Discord context (used to determine language from server)
        lang: Language code ('fr' or 'en'). If None, will be determined from ctx
    """
    # Determine language from context if not provided
    if lang is None:
        if ctx is not None:
            guild_id = ctx.guild.id if ctx.guild is not None else None
            lang = language_manager_instance.get_server_language(guild_id)
        else:
            lang = "en"
    
    if tuto_name == "":
        tuto_name = "tuto.txt"
    else:
        tuto_name = tuto_name.lower()
        tuto_name = f'tuto_{tuto_name}.txt'
    
    # Try language-specific file first
    lang_specific_file = f'tuto_texts/{lang}/{tuto_name}'
    try:
        with open(lang_specific_file, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        pass
    
    # Fallback to default language file (existing structure)
    default_file = f'tuto_texts/{tuto_name}'
    try:
        with open(default_file, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"Tutorial '{tuto_name}' not found."


