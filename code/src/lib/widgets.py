from ST7735 import TFT
from sysfont import sysfont

class SelectableWidget():
    def __init__(self, display:TFT, pos:tuple, text:str, on_execute):
        self.pos = pos
        self.text = text
        self.display = display
        self.function = on_execute

        self.display.text((self.pos[0]+4, self.pos[1]+2), self.text, TFT.WHITE, sysfont, 1)

    def clear(self):
        self.display.fillrect(self.pos, (6*len(self.text)+8, self.pos[0]+8), TFT.BLACK)

    def on_stop_hover(self):
        self.clear()
        self.display.text((self.pos[0]+4, self.pos[1]+2), self.text, TFT.WHITE, sysfont, 1)

    def on_hover(self):
        self.display.rect(self.pos, (6*len(self.text)+8, self.pos[0]+8), TFT.WHITE)
        self.display.text((self.pos[0]+4, self.pos[1]+2), self.text, TFT.WHITE, sysfont, 1)

    def on_click(self):
        self.function()
