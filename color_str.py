class CText:
    '''
    Class used to create colorized text
    '''

    text = ""

    def __init__(self, text: str|None = None):
        if text:
            self.text += text

    def txt(self, text):
        self.text += text
        return self
    def red(self, text):
        self.text += red(text)
        return self
    def pink(self, text):
        self.text += pink(text)
        return self
    def blue(self, text):
        self.text += blue(text)
        return self
    def green(self, text):
        self.text += green(text)
        return self
    def yellow(self, text):
        self.text += yellow(text)
        return self

    def str(self):
        return str(self)

    def __str__(self):
        return "```ansi\n" + self.text+"\n```"
    def __add__(self, other):
        return CText(self.text + other.text)
    def __iadd__(self, other):
        self.text += other.text
        return self

#pour coloriser il faut mettre ```ansi\n

def red(text:str):
    return f"[2;31m[1;31m{text}[0m[2;31m[0m"


def pink(text:str):
    return f"[2;35m[1;35m{text}[0m[2;35m[0m"


def blue(text:str):
    return f"[2;34m[1;34m{text}[0m[2;34m[0m"

def green(text:str):
    return f"[2;32m[1;32m{text}[0m[2;32m[0m"


def yellow(text:str):
    return f"[2;33m[1;33m{text}[0m[2;33m[0m"