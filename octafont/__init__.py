from importlib.resources import files

from octafont import pixelfont
from octafont.pixelfont import PixelFont, PixelFontVariant


class Octafont(PixelFont):

    def __init__(self):
        super().__init__(
            files('octafont').joinpath('pixeldata').joinpath('octafont.png').read_bytes(),
            {PixelFontVariant.NORMAL: 9, PixelFontVariant.BOLD: 0},
            3, 1, 8
        )

    def _build_codepage(self) -> dict[str, int]:
        codepage = {
            'Ä': 94, 'Ö': 95, 'Ü': 96,
            'ä': 97, 'ö': 98, 'ß': 99, 'ü': 100,
            '€': 101,
            '°': 102,
            '🡡': 103, '🡥': 104, '🡢': 105, '🡦': 106, '🡣': 107, '🡧': 108, '🡠': 109, '🡤': 110,
            '💧': 111, '❄': 112, '👁': 113
        }

        for i in range(33, 127):
            codepage[chr(i)] = i - 33

        return codepage


class Hexafont(PixelFont):

    def __init__(self):
        super().__init__(
            files('octafont').joinpath('pixeldata').joinpath('hexafont.png').read_bytes(),
            {PixelFontVariant.NORMAL: 0},
            6, 2, 16
        )

    def _build_codepage(self) -> dict[str, int]:
        return dict((chr(i), i - 48) for i in range(48, 59))
