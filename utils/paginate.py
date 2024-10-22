import discord
from discord.ext.commands import Context
from utils.color_str import CText


class PaginatorView(discord.ui.View):
    def __init__(self, pages:list[discord.Embed], timeout=60):
        super().__init__(timeout=timeout)
        self.pages = pages
        for p in self.pages:
            p.set_footer(text=f"{self.pages.index(p)+1}/{len(self.pages)}")
        self.current_page = 0

    async def send_initial_message(self, ctx:Context):
        # Envoyer la première page
        return await ctx.send(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Naviguer à la page précédente
        if self.current_page == 0:
            self.current_page = len(self.pages) - 1
        else:
            self.current_page -= 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Naviguer à la page suivante
        if self.current_page == len(self.pages) - 1:
            self.current_page = 0
        else:
            self.current_page += 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)


def split_text_into_pages(text:str, max_chars=1900)->list[discord.Embed]:
    lines = text.split('\n')
    pages = []
    current_page = ""

    for line in lines:
        if len(current_page) + len(line) + 1 > max_chars:  # +1 pour le '\n'
            embed = discord.Embed(description=current_page)
            pages.append(embed)
            current_page = line
        else:
            if current_page:
                current_page += '\n'
            current_page += line

    if current_page:
        embed = discord.Embed(description=current_page)
        pages.append(embed)

    return pages

async def paginate(ctx:Context, txt: str):
    # Diviser le texte en pages
    pages = split_text_into_pages(txt)

    if len(pages) > 1:
        # Créer la vue de pagination et envoyer le premier message
        view = PaginatorView(pages)
        await view.send_initial_message(ctx)
    else:
        # Si le texte tient sur une seule page, pas besoin de pagination
        await ctx.send(txt)

## Paginate with DICT ///////////////////////////////////////////////////////////////////////////////////////////////////////////

def create_embeds_from_dict(dict_text:dict[str,str], max_chars=800)->list[discord.Embed]:
    pages = []
    
    for title, text in dict_text.items():
        lines = text.split('\n')
        current_page = ""
        
        for line in lines:
            if len(current_page) + len(line) + 1 > max_chars:  # +1 pour le '\n'
                embed = discord.Embed(title=title, description=current_page)
                pages.append(embed)
                current_page = line
            else:
                if current_page:
                    current_page += '\n\n'
                current_page += line
        
        if current_page:
            embed = discord.Embed(title=title, description=current_page)
            pages.append(embed)

    return pages

async def paginate_dict(ctx:Context, dict_text:dict[str, str]):
    # Créer les pages (embeds) à partir de la map
    pages = create_embeds_from_dict(dict_text)

    if len(pages) > 1:
        # Créer la vue de pagination et envoyer le premier embed
        view = PaginatorView(pages)
        await view.send_initial_message(ctx)
    else:
        # Si une seule page, pas besoin de pagination
        await ctx.send(embed=pages[0])