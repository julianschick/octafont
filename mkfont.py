from PIL import Image
from bitarray import bitarray
from os import listdir, makedirs
from os.path import realpath, dirname, join, isfile, basename, splitext, exists

here = dirname(realpath(__file__))
input_dir = join(here, "pixeldata")
input_files = [join(input_dir, f) for f in listdir(input_dir) if isfile(join(input_dir, f)) and f.lower().endswith(".png")]

if not exists('output'):
    makedirs('output')


def extract_pixel_data(img, marker_line):
    result = []
    inside_character = False
    for i in range(0, img.width):
        p = img.getpixel((i, marker_line))

        if p == (255, 0, 0):
            if not inside_character:
                inside_character = True
                start = i
        elif p == (0, 255, 0):
            if inside_character:
                result.append((start, i))
                inside_character = False
            else:
                result.append((i, i))

    return result


def build_tables(img, bounds, y_pos):
    jumps, widths, chars = [], [], []

    cursor = 0
    counter = 0
    for i in range(0, 256):
        table_index = get_char_mapping(i)
        if table_index != -1:
            (start, end) = bounds[table_index]
            width = end - start + 1
            jumps.append(("\n    " if i % 16 == 0 and i else "") + str(cursor).rjust(5))
            widths.append(("\n    " if i % 16 == 0 and i else "") + str(width).rjust(2))

            for x in range(start, end + 1):
                bits = bitarray(endian="little")
                for y in range(y_pos, y_pos + 8):
                    p = img.getpixel((x, y))
                    if p == (0, 0, 0):
                        bits.append(1)
                    else:
                        bits.append(0)
                byte = bits.tobytes()[0]

                if x == start:
                    b = bytearray([i])
                    comment = "/* " + b.decode("iso8859-15") + " */  "
                else:
                    comment = ""

                chars.append(("\n    " if x == start and counter else "") + comment + f"{byte:#04x}")

            cursor += width
            counter += 1
        else:
            jumps.append(("\n    " if i % 16 == 0 and i else "") + str(-1).rjust(5))
            widths.append(("\n    " if i % 16 == 0 and i else "") + str(-1).rjust(2))

    jumps_str = ", ".join(jumps)
    widths_str = ", ".join(widths)
    chars_str = ", ".join(chars)

    return jumps_str, widths_str, chars_str


# ISO-8859-15
def get_char_mapping(v):
    # Special supported characters from upper block
    if v == 0xc4: return 94  # Ä
    if v == 0xd6: return 95  # Ö
    if v == 0xdc: return 96  # Ü
    if v == 0xe4: return 97  # ä
    if v == 0xf6: return 98  # ö
    if v == 0xdf: return 99  # ß
    if v == 0xfc: return 100 # ü
    if v == 0xa4: return 101 # €

    # ASCII block (non control chars up to 127)
    if 33 <= v <= 126:
        return v - 33

    # No mapping
    return -1


def print_char(img, bounds, variant, v):
    index = get_char_mapping(0xdf)

    if index != -1:
        (start, end) = bounds[index]

        for y in range(variant["y_pos"], variant["y_pos"] + 8):
            for x in range(start, end + 1):
                p = img.getpixel((x, y))
                if p == (0, 0, 0):
                    print("x", end='')
                else:
                    print(" ", end='')
            print("")
    else:
        print("No character data.")


for input_file in input_files:

    img = Image.open(input_file)
    font_name = splitext(basename(input_file))[0].capitalize()

    variants = [
        {"name": "Regular", "marker_line": 9, "y_pos": 10},
        {"name": "Bold", "marker_line": 0, "y_pos": 1}
    ]

    for v in variants:
        bounds = extract_pixel_data(img, v["marker_line"])
        variant = v["name"]
        (jumps, widths, chars) = build_tables(img, bounds, v["y_pos"])

        #print_char(img, bounds, v, 0xdf)

        h_file = f"""#ifndef {font_name.upper()}_{variant.upper()}_H_
    #define {font_name.upper()}_{variant.upper()}_H_
    
    #include "pixelfont.h"
    
    class {font_name}{variant} : public PixelFont {{
    
    private:
        static const uint8_t chars[];
        static const int jumps[];
        static const int widths[];
    
        const uint8_t* get_chars() override {{
            return chars;
        }}
    
        const int* get_jumps() override {{
            return jumps;
        }}
    
        const int* get_widths() override {{
            return widths;
        }}
    }};
    
    const uint8_t {font_name}{variant}::chars[] = {{
    {chars}
    }};
    
    const int {font_name}{variant}::jumps[] = {{
    {jumps}
    }};
    
    const int {font_name}{variant}::widths[] = {{
    {widths}
    }};
    
    #endif //{font_name.upper()}_{variant.upper()}_H_
    """
        output_file = join(here, "output", font_name.lower() + f"-{variant.lower()}.h")
        print(basename(input_file) + " -> " + basename(output_file))

        f = open(output_file, "w")
        f.write(h_file)
        f.close()
