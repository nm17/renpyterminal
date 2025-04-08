"""renpy
init -500 python:
"""

__all__ = []

def setup_fonts():
    # (font, bold, italics)
    config.font_replacement_map["terminal", False, False] = (
        "terminal/fonts/IosevkaTerm-Medium.ttf",
        False,
        False,
    )
    config.font_replacement_map["terminal", False, True] = (
        "terminal/fonts/IosevkaTerm-MediumItalic.ttf",
        False,
        False,
    )
    config.font_replacement_map["terminal", True, False] = (
        "terminal/fonts/IosevkaTerm-Bold.ttf",
        False,
        False,
    )
    config.font_replacement_map["terminal", True, True] = (
        "terminal/fonts/IosevkaTerm-BoldItalic.ttf",
        False,
        False,
    )

setup_fonts()