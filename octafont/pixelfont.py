import io

from PIL import Image
from typing import Tuple, Optional
from enum import Enum

from octafont.rect import Rect


class PixelFontVariant(Enum):
    NORMAL = 0
    BOLD = 1


V = PixelFontVariant


class SpecialChar(Enum):
    SPACE = 0
    LINEBREAK = 1


class TextAlignment(Enum):
    LEFT = 0
    RIGHT = 1
    CENTERED = 2


class PixelCharacterMetrics:
    def __init__(
            self,
            char: 'PixelCharacter',
            spacing_before: int,
            x_before: int,
            x_after: int,
            y_before: int
    ):
        self.char = char
        self.spacing_before = spacing_before
        self.x_before = x_before
        self.x_after = x_after
        self.y_before = y_before


class LineMetrics:
    def __init__(self, chars: list[PixelCharacterMetrics], y_pos: int, font: 'PixelFont'):
        self.chars = chars
        self.width = chars[-1].x_after if chars else 0
        self.y_pos = y_pos
        self.y_after = y_pos + font.height


class PixelCharacter:
    def __init__(self, pixels: list[list[bool]], auto_undercut: bool = True):
        self._pixels = pixels
        self._auto_undercut = auto_undercut

        if len(pixels) == 0 or len(pixels[0]) == 0:
            raise RuntimeError("Empty pixel data not allowed")
        if len(set(map(lambda col: len(col), pixels))) > 1:
            raise RuntimeError("Pixel data has to be quadratic")

    @property
    def width(self) -> int:
        return len(self._pixels)

    @property
    def height(self) -> int:
        return len(self._pixels[0])

    def get_undercut(self, following_char: 'PixelCharacter') -> int:
        if not self._auto_undercut:
            return 0

        last_col = self._pixels[self.width - 1]
        first_col = following_char._pixels[0]

        for i in range(0, len(last_col)):
            if (last_col[i] and first_col[i]) or \
               (i+1 < len(last_col) and last_col[i] and first_col[i+1]) or \
               (i-1 >= 0 and last_col[i] and first_col[i-1]):
                return 0

        return 1

    def draw(self, img: Image, box: 'Rect', color: Tuple[int, int, int] = (0, 0, 0)) -> Optional[Tuple[int, int]]:
        if not color >= (0, 0, 0) or not color <= (255, 255, 255):
            raise RuntimeError("Invalid color value")

        box = box.intersect(Rect.from_image_dimensions(img))
        if box.is_empty():
            return None

        max_x, max_y = -1, -1

        for cx in range(0, self.width):
            for cy in range(0, self.height):
                if box.contains_point((box.x + cx, box.y + cy)) and self._pixels[cx][cy]:
                    img.putpixel((box.x + cx, box.y + cy), color)
                    max_x, max_y = max(box.x + cx, max_x), max(box.y + cy, max_y)

        return None if max_x == -1 else max_x, max_y

    def __str__(self):
        result = ''
        for y in range(0, self.height):
            result += ''.join(map(lambda i: 'O' if self._pixels[i][y] else ' ', range(self.width)))
            if y < self.height - 1:
                result += '\n'

        return result


class PixelFont:

    def __init__(
            self,
            image_bytes: bytes,
            variants: dict[PixelFontVariant, int],
            space_width: int,
            character_spacing: int,
            height: int = 8
    ):
        img = Image.open(io.BytesIO(image_bytes))

        if not variants:
            RuntimeError('At least one font variant has to be given')

        if PixelFontVariant.NORMAL not in variants:
            variants[PixelFontVariant.NORMAL] = list(variants.values())[0]

        state_in_char: bool = False
        char_data: list[list[bool]] = []
        self._characters: dict[PixelFontVariant, list[PixelCharacter]] = {}
        self._space_width = space_width
        self._character_spacing = character_spacing
        self._height = height
        self._codepage = self._build_codepage()

        for (variant, y_marker) in variants.items():
            chars = []
            for x in range(0, img.width):
                marker_pixel: Tuple[int, int] = img.getpixel((x, y_marker))

                # red marker = char begin
                if marker_pixel == (255, 0, 0):
                    if not state_in_char:
                        state_in_char = True
                        char_data.append(self._extract_column(img, x, y_marker + 1))

                # green marker = char end
                elif marker_pixel == (0, 255, 0):
                    # end of multi-column character
                    if state_in_char:
                        state_in_char = False
                        char_data.append(self._extract_column(img, x, y_marker + 1))

                    # single column character
                    else:
                        char_data = [(self._extract_column(img, x, y_marker + 1))]

                    chars.append(PixelCharacter(char_data))
                    char_data = []

                # no marker
                else:
                    if state_in_char:
                        char_data.append(self._extract_column(img, x, y_marker + 1))

            if state_in_char:
                chars.append(PixelCharacter(char_data))

            self._characters[variant] = chars

    def _build_codepage(self):
        raise NotImplementedError

    def _extract_column(self, img: Image, x: int, y_start: int) -> list[bool]:
        col_data = [False for _ in range(self._height)]
        for y in range(y_start, y_start + self._height):
            col_data[y - y_start] = True if img.getpixel((x, y)) != (255, 255, 255) else False
        return col_data

    def _get_char_index(self, unicode_char: str) -> Optional[int]:
        return self._codepage.get(unicode_char[0])

    @property
    def height(self):
        return self._height

    def get_character(self, c: str, variant: PixelFontVariant = PixelFontVariant.NORMAL) -> Optional[PixelCharacter]:
        if not self._characters[variant]:
            return None

        index: int = self._get_char_index(c)
        return self._characters[variant][index] if index is not None else None

    def _metrics(self,
                 message: str,
                 variant_map: list[PixelFontVariant],
                 base_variant: PixelFontVariant = V.NORMAL,
                 break_width: Optional[int] = None) -> list[LineMetrics]:

        effective_variant_map = \
            [variant_map[i] if i < len(variant_map) else base_variant for i in range(len(message))]

        chars = []
        for (char, variant) in zip(message, effective_variant_map):
            if char in (" ", "\t"):
                chars.append(SpecialChar.SPACE)
            elif char in ("\r", "\n"):
                chars.append(SpecialChar.LINEBREAK)
            else:
                chars.append(self.get_character(char, variant))

        lines = []
        specials = []
        char_before: Optional[PixelCharacter] = None

        x_cursor, y_cursor = 0, 0
        current_line = []  # (char, spacing_before, width, x_before, x_after, y_before)
        for char in chars:
            if type(char) is SpecialChar:
                specials.append(char)
                char_before = None
            elif type(char) is PixelCharacter:
                if SpecialChar.LINEBREAK in specials:
                    last_line_break = next(
                        i for i in reversed(range(len(specials))) if specials[i] == SpecialChar.LINEBREAK)
                else:
                    last_line_break = -1
                spaces = len(specials) - 1 - last_line_break
                breaks = sum(1 for _ in filter(lambda s: s == SpecialChar.LINEBREAK, specials))
                if breaks > 0:
                    y_cursor += self._height * breaks
                    x_cursor = 0
                    lines.append(LineMetrics(current_line, y_cursor, self))
                    current_line = []
                specials.clear()

                spacing_before = self._character_spacing if char_before else spaces * self._space_width
                if char_before:
                    spacing_before -= char_before.get_undercut(char)

                if break_width and x_cursor + char.width + spacing_before >= break_width:
                    x_cursor = 0
                    lines.append(LineMetrics(current_line, y_cursor, self))
                    current_line = []
                    y_cursor += self._height
                    spacing_before = 0

                current_line.append(
                    PixelCharacterMetrics(
                        char,
                        spacing_before,
                        x_cursor,
                        x_cursor + char.width + spacing_before,
                        y_cursor
                    )
                )

                x_cursor += char.width + spacing_before
                char_before = char

        if current_line:
            lines.append(LineMetrics(current_line, y_cursor, self))

        return lines

    def metrics(
            self,
            message: str,
            variant_map=None, variant: PixelFontVariant = PixelFontVariant.NORMAL
    ) -> Tuple[int, int]:

        if variant_map is None:
            variant_map = []

        lines = self._metrics(message, base_variant=variant, variant_map=variant_map, break_width=None)
        if lines:
            width = max(map(lambda line: line.width, lines))
            height = lines[-1].y_after
            return width, height
        else:
            return 0, 0

    def draw(self,
             message: str,
             img: Image,
             box: Optional[Rect] = None,
             variant_map=None,
             variant: PixelFontVariant = PixelFontVariant.NORMAL,
             wrap_text: bool = False, clip_whole_chars: bool = False,
             text_alignment: TextAlignment = TextAlignment.LEFT,
             color: Tuple[int, int, int] = (0, 0, 0)):

        if variant_map is None:
            variant_map = []

        if box is None:
            box = Rect.from_image_dimensions(img)

        if not color >= (0, 0, 0) or not color <= (255, 255, 255):
            raise RuntimeError("Invalid color value")

        for line in self._metrics(
                message,
                variant_map=variant_map,
                base_variant=variant,
                break_width=box.width if wrap_text else None
        ):
            for metrics in line.chars:
                x_shift_alignment = 0
                if text_alignment == TextAlignment.RIGHT:
                    x_shift_alignment = max(0, box.width - line.width)
                elif text_alignment == TextAlignment.CENTERED:
                    x_shift_alignment = max(0, (box.width - line.width) // 2)

                char_x = box.x + metrics.x_before + metrics.spacing_before + x_shift_alignment
                char_y = box.y + metrics.y_before
                char_box = Rect(char_x, char_y, metrics.char.width, self._height)

                if box.contains_rect(char_box.get_inner_rect()) or not clip_whole_chars:
                    metrics.char.draw(img, char_box.intersect(box), color=color)
