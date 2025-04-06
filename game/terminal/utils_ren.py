"""renpy
init -400 python:
"""

class Colors:
    """ANSI color codes"""

    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"

import functools

@renpy.pure
@functools.lru_cache
def to_hex_color(color_str, isFg):
    """
    Convert ANSI color names to hex codes. Returns hex inputs unchanged.

    Args:
        color_str (str): Color name (e.g., 'green', 'bright_red') or hex code
        default (str): Default color to return if input is invalid (optional)

    Returns:
        str: Hex color code (or default if invalid)
    """
    # Check if input is a valid hex color code (3, 4, 6, or 8 digits with optional #)
    if re.match(
        r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", color_str
    ):
        return color_str

    if color_str == "default":
        if isFg:
            return "#ffffff"
        else:
            return "#000000"

    # ANSI color name to hex mapping (standard 16-color palette)
    ansi_colors = {
        # Normal colors
        "black": "#000000",
        "red": "#ff0000",
        "green": "#00ff00",
        "yellow": "#ffff00",
        "blue": "#0000ff",
        "magenta": "#ff00ff",
        "cyan": "#00ffff",
        "white": "#ffffff",
        # Bright colors
        "bright_black": "#808080",
        "bright_red": "#ff5555",
        "bright_green": "#55ff55",
        "bright_yellow": "#ffff55",
        "bright_blue": "#5555ff",
        "bright_magenta": "#ff55ff",
        "bright_cyan": "#55ffff",
        "bright_white": "#ffffff",
    }

    # Normalize input name (case-insensitive, spaces to underscores)
    normalized = color_str.lower().replace(" ", "_")
    return ansi_colors.get(normalized, None)
