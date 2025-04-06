"""renpy
init -500 python:
"""

# (font, bold, italics)
config.font_replacement_map["terminal", False, False] = (
    "IosevkaTerm-Medium.ttf",
    False,
    False,
)
config.font_replacement_map["terminal", False, True] = (
    "IosevkaTerm-MediumItalic.ttf",
    False,
    False,
)
config.font_replacement_map["terminal", True, False] = (
    "IosevkaTerm-Bold.ttf",
    False,
    False,
)
config.font_replacement_map["terminal", True, True] = (
    "IosevkaTerm-BoldItalic.ttf",
    False,
    False,
)
