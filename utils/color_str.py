class CText:
    '''
    Class used to create colorized text
    '''

    def __init__(self, text: str|None = None):
        self.nodes: list[TextNode] = []
        if text:
            self.nodes += [TextNode(text)]

    def txt(self, text):
        self.nodes.append(TextNode(text))
        return self
    def red(self, text):
        self.nodes.append(RedNode(text))
        return self
    def pink(self, text):
        self.nodes.append(PinkNode(text))
        return self
    def blue(self, text):
        self.nodes.append(BlueNode(text))
        return self
    def green(self, text):
        self.nodes.append(GreenNode(text))
        return self
    def yellow(self, text):
        self.nodes.append(YellowNode(text))
        return self

    def str(self):
        return self.__str__()
    def raw(self):
        return "".join(n.raw() for n in self.nodes)

    def __str__(self):
        inner = "".join(n.colorized() for n in self.nodes)
        return "```ansi\n" + inner + "\n```"



    def __add__(self, other):
        match other:
            case CText():
                ntxt = CText()
                ntxt.nodes = self.nodes + other.nodes
                return ntxt
            case str():
                ntxt = CText()
                ntxt.nodes += self.nodes + [TextNode(other)]
                return ntxt
            case _:
                return NotImplemented
    def __iadd__(self, other):
        match other:
            case CText():
                self.nodes += other.nodes
            case str():
                self.nodes += [TextNode(other)]
            case _:
                return NotImplemented
        return self

#pour coloriser il faut mettre ```ansi\n

class TextNode():
    def __init__(self, txt: str):
        self.txt = txt
    
    def raw(self) -> str:
        return self.txt

    colorized = raw

class RedNode(TextNode):
    def colorized(self):
        return f"[2;31m[1;31m{self.txt}[0m[2;31m[0m"

class PinkNode(TextNode):
    def colorized(self):
        return f"[2;35m[1;35m{self.txt}[0m[2;35m[0m"

class BlueNode(TextNode):
    def colorized(self):
        return f"[2;34m[1;34m{self.txt}[0m[2;34m[0m"

class GreenNode(TextNode):
    def colorized(self):
        return f"[2;32m[1;32m{self.txt}[0m[2;32m[0m"

class YellowNode(TextNode):
    def colorized(self):
        return f"[2;33m[1;33m{self.txt}[0m[2;33m[0m"