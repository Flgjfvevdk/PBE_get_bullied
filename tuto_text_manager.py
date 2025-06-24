

def getTuto(tuto_name:str):
    """
    Returns the tutorial text for the given tutorial name.
    """
    if tuto_name == "":
        tuto_name = "tuto.txt"
    else :
        tuto_name = tuto_name.lower()
        tuto_name = f'tuto_{tuto_name}.txt'
    try:
        with open(f'tuto_texts/{tuto_name}', 'r', encoding='utf-8') as file:
            return "___________________\n"+file.read() + "\n___________________"
    except FileNotFoundError:
        print(f"Tutorial file '{tuto_name}' not found.")
        return None


