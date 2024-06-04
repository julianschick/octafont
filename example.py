from PIL import Image

from octafont import Octafont, Hexafont
from octafont.pixelfont import TextAlignment

octa = Octafont()
hexa = Hexafont()

img = Image.new("RGB", (100, 8), color=(255, 255, 255))
octa.draw("Hello World", img)
img.save("/tmp/test8.png", format="png")

img = Image.new("RGB", (100, 16), color=(255, 255, 255))
hexa.draw("12:33", img, text_alignment=TextAlignment.CENTERED)
img.save("/tmp/test16.png", format="png")
