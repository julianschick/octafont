# Octafont (and Hexafont)

![Example image](/img/example.png)

Pixelfont designed for flipdot matrices. Each text line has a height of 8 pixels and the characters, 
in favor of a natural appearance, have variable width (1 to 6 pixels).
The bottom most pixel line is kept free by normal letters and only used by letters that go below the baseline, 
as for instance "g" or "q". A bold and a regular version is available. 
**Octafont's** look-and-feel is inspired by the Brose flipdot font that was still shown on my flipdot modules I got 
directly out of a bus. It is only inspired and not a clone, as the display did not show all characters, 
so the unknown ones were merely created in the same spirit.  Octafont is available in normal weight and as bold font.
The font is intended for usage in python scripts and can be rendered to PIL images.

The font currently provides all printable ASCII characters, some german special letters from the upper block and
some unicode icons. The drawing routines for the font expect unicode strings as input and will skip every letter 
they don't have a symbol for.

Also part of this package is **Hexafont**. As the name might suggest, it is 16 pixels
high instead of 8. For the time being this font only contains numbers and the colon, as
it is mainly intended for displaying times.

**Example Usage:**
```python
from PIL import Image

from octafont import Octafont, Hexafont
from octafont.pixelfont import TextAlignment
from octafont.rect import Rect

octa = Octafont()
hexa = Hexafont()

img = Image.new("RGB", (100, 8), color=(255, 255, 255))
octa.draw("Hello World", img, Rect.from_image_dimensions(img))
img.save("test8.png", format="png")

img = Image.new("RGB", (100, 16), color=(255, 255, 255))
hexa.draw("12:33", img, Rect.from_image_dimensions(img), text_alignment=TextAlignment.CENTERED)
img.save("test16.png", format="png")
```

**C++**

In the folder `cpp-generator` There is some old, unmaintained code, which can generate a C++ class
for accessing the pixel data of the font in form of octets. Check the old [README](cpp-generator/README.md).



