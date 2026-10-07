import curses
from dataclasses import dataclass

ESCAPE = "\x1b"
TAB_KEYS = {"\t", curses.KEY_BTAB, curses.KEY_DOWN, curses.KEY_UP}
ENTER_KEYS = {"\n", "\r", curses.KEY_ENTER}
BACKSPACE_KEYS = {"\x7f", "\b", curses.KEY_BACKSPACE}
CLEAR_KEY = "\x03"
BUTTONS = (" ↵ save ", " tab switch ", " ^c clear ", " esc cancel ")
BUTTON_GAP = 2
# Catppuccin Mocha as (24-bit RGB, xterm-256 index, 8-color fallback).
PALETTE = {
    "accent": (0x89B4FA, 111, curses.COLOR_BLUE),
    "text": (0xCDD6F4, 189, curses.COLOR_WHITE),
    "dim": (0x6C7086, 243, curses.COLOR_WHITE),
    "surface": (0x313244, 236, curses.COLOR_BLACK),
    "panel": (0x181825, 234, curses.COLOR_BLACK),
    "error": (0xF38BA8, 211, curses.COLOR_RED),
}
DIRECT_COLORS = 1 << 24
PAIRS = {
    "base": ("text", "panel"),
    "label": ("dim", "panel"),
    "active_label": ("accent", "panel"),
    "input": ("text", "surface"),
    "primary": ("panel", "accent"),
    "button": ("text", "surface"),
    "error": ("error", "panel"),
}


@dataclass
class Field:
    label: str
    text: str
    max_length: int | None = None

    def __post_init__(self):
        self.cursor = len(self.text)

    def handle(self, key):
        if key in BACKSPACE_KEYS and self.cursor > 0:
            self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
            self.cursor -= 1
        elif key == curses.KEY_DC:
            self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
        elif key == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor = min(len(self.text), self.cursor + 1)
        elif key == curses.KEY_HOME:
            self.cursor = 0
        elif key == curses.KEY_END:
            self.cursor = len(self.text)
        elif isinstance(key, str) and key.isprintable() and not self.is_full():
            self.text = self.text[:self.cursor] + key + self.text[self.cursor:]
            self.cursor += 1

    def clear(self):
        self.text, self.cursor = "", 0

    def is_full(self):
        return self.max_length is not None and len(self.text) >= self.max_length


def visible_slice(field, width):
    start = max(0, field.cursor - width + 1)
    return field.text[start:start + width], field.cursor - start


def init_styles():
    if not curses.has_colors():
        return {name: curses.A_NORMAL for name in PAIRS} | {"primary": curses.A_REVERSE}
    depth = 0 if curses.COLORS >= DIRECT_COLORS else 1 if curses.COLORS >= 256 else 2

    def color(name):
        return PALETTE[name][depth]

    styles = {}
    for number, (name, (fg, bg)) in enumerate(PAIRS.items(), start=1):
        curses.init_pair(number, color(fg), color(bg))
        styles[name] = curses.color_pair(number)
    styles["active_label"] |= curses.A_BOLD
    styles["primary"] |= curses.A_BOLD
    styles["button"] |= curses.A_BOLD
    return styles


def field_row(index):
    return index * 3


def draw_buttons(screen, styles, row, width):
    total = sum(len(label) for label in BUTTONS) + BUTTON_GAP * (len(BUTTONS) - 1)
    column = max(0, (width - total) // 2)
    for index, label in enumerate(BUTTONS):
        style = styles["primary"] if index == 0 else styles["button"]
        screen.addnstr(row, column, label, max(0, width - 1 - column), style)
        column += len(label) + BUTTON_GAP


def draw(screen, styles, fields, active, message):
    screen.erase()
    height, width = screen.getmaxyx()
    input_width = max(1, width)
    for index, field in enumerate(fields):
        row = field_row(index)
        label_style = styles["active_label" if index == active else "label"]
        text, _ = visible_slice(field, input_width - 1)
        screen.addnstr(row, 0, field.label, width - 1, label_style)
        screen.addnstr(row + 1, 0, f" {text}".ljust(input_width), input_width, styles["input"])
    buttons_row = height - 1
    if message:
        screen.addnstr(buttons_row - 1, 0, message, width - 1, styles["error"])
    draw_buttons(screen, styles, buttons_row, width)
    _, cursor = visible_slice(fields[active], input_width - 1)
    screen.move(field_row(active) + 1, 1 + cursor)
    screen.refresh()


def run_form(screen, fields, on_submit):
    """on_submit returns an error message to keep the form open, or None to close it."""
    curses.raw()
    curses.curs_set(1)
    styles = init_styles()
    screen.bkgd(" ", styles["base"])
    active, message = 0, None
    while True:
        draw(screen, styles, fields, active, message)
        key = screen.get_wch()
        message = None
        if key == ESCAPE:
            return False
        if key in ENTER_KEYS:
            message = on_submit(*(field.text for field in fields))
            if message is None:
                return True
        elif key in TAB_KEYS:
            active = (active + 1) % len(fields)
        elif key == CLEAR_KEY:
            fields[active].clear()
        else:
            fields[active].handle(key)
