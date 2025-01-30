import discord

def create_embed(
    title: str, 
    description_lines: list[str], 
    file: discord.File | None = None, 
    footnote: str | None = None, 
    thumbnail: str | None = None, 
    color: int = 0x3498db, 
    columns: int = 1, 
    str_between_element: str = "\n\n"
) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)

    if file:
        embed.set_image(url=f"attachment://{file.filename}")

    if footnote:
        embed.set_footer(text=footnote)

    if thumbnail:
        print("thumbnail is ", thumbnail)
        embed.set_thumbnail(url=thumbnail)

    # If one column, set as a simple description
    if columns == 1 or len(description_lines) == 1:
        description = ""
        for line in description_lines:
            description += line + str_between_element
        
        embed.description = description
    else:
        # Split into multiple fields
        col_size = (len(description_lines) + columns - 1) // columns  # Distribute evenly
        for i in range(columns):
            chunk = description_lines[i * col_size : (i + 1) * col_size]
            if chunk:
                embed.add_field(name="", value=f"{str_between_element}".join(chunk), inline=True)
    return embed
