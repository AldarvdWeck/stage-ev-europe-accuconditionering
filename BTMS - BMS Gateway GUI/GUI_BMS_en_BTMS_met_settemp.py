import os
import sys
import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports
import threading
import queue
import time
import re

try:
    import tksvg
except ImportError:
    print("tksvg is niet geinstalleerd.")
    print("Installeer met: pip install tksvg")
    raise

try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageTk = None


BAUDRATE = 115200
MANUAL_SET_TEMP_MIN = 1
MANUAL_SET_TEMP_MAX = 50



def app_dir():
    """Map waar resources staan. Werkt als .py en als PyInstaller .exe."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(__file__))


def read_svg_with_color(path, color):
    """Lees de SVG en vervang currentColor door de gewenste kleur."""
    with open(path, "r", encoding="utf-8") as file:
        svg_text = file.read()

    svg_text = svg_text.replace("currentColor", color)
    return svg_text


def load_svg(path, color, size=58):
    """Laad een SVG met tksvg en forceer de grootte in de SVG zelf."""
    svg_text = read_svg_with_color(path, color)

    svg_text = re.sub(r'width="[^"]*"', f'width="{size}"', svg_text, count=1)
    svg_text = re.sub(r'height="[^"]*"', f'height="{size}"', svg_text, count=1)

    return tksvg.SvgImage(data=svg_text, format=f"svg -scaletoheight {size}")


def mode_to_text(value):
    try:
        value = int(value)
    except Exception:
        return "-"

    return {
        0: "Shutdown",
        1: "Cooling",
        2: "Heating",
        3: "Self recycling",
    }.get(value, f"Unknown ({value})")


def relay_to_text(value):
    try:
        value = int(value)
    except Exception:
        return "-"

    return {
        0: "Open",
        1: "Closed",
    }.get(value, f"Unknown ({value})")


def error_level_to_text(value):
    try:
        value = int(value)
    except Exception:
        return "-"

    return {
        0: "No error",
        1: "Level 1",
        2: "Level 2",
        3: "Level 3",
    }.get(value, f"Unknown ({value})")


def error_code_to_text(value):
    try:
        value = int(value)
    except Exception:
        return "-"

    return {
        0: "Geen fout",
        1: "PTC level 1 fault",
        2: "PTC overvoltage",
        5: "PTC undervoltage",
        11: "PTC / NTC fault",
        14: "PTC communication fault",
        19: "Compressor fault",
        20: "HV supply fault",
        21: "Fan fault",
        22: "High pressure sensor fault",
        23: "Low pressure sensor fault",
        24: "Inlet temp sensor fault",
        25: "Outlet temp sensor fault",
        26: "Ambient temp sensor fault",
        27: "Water pump fault",
        30: "Water level sensor fault",
        31: "PTC overtemperature",
        47: "LV supply fault",
        48: "BMS/TMS CAN communication fault",
        51: "Anti-freeze temp sensor fault",
    }.get(value, f"Foutcode {value}")


def parse_line(line):
    data = {}

    parts = line.strip().split(";")
    for part in parts:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        data[key.strip()] = value.strip()

    return data


class RoundedCard(tk.Frame):
    def __init__(
        self,
        parent,
        bg="#ffffff",
        border="#dfe5ec",
        parent_bg="#f7f9fb",
        radius=12,
        padding=0,
        **kwargs
    ):
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0, **kwargs)

        self.fill_color = bg
        self.border_color = border
        self.parent_bg = parent_bg
        self.radius = radius
        self.padding = padding

        self.canvas = tk.Canvas(
            self,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            relief="flat"
        )
        self.canvas.pack(fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg, bd=0, highlightthickness=0)
        self.window_id = self.canvas.create_window(
            self.padding,
            self.padding,
            window=self.inner,
            anchor="nw"
        )

        self.canvas.bind("<Configure>", self._on_resize)

    def _rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _on_resize(self, event):
        width = event.width
        height = event.height

        self.canvas.delete("card_shape")

        if width <= 2 or height <= 2:
            return

        self._rounded_rectangle(
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=self.border_color,
            outline=self.border_color,
            tags="card_shape"
        )

        self._rounded_rectangle(
            2,
            2,
            width - 2,
            height - 2,
            max(1, self.radius - 1),
            fill=self.fill_color,
            outline=self.fill_color,
            tags="card_shape"
        )

        inner_width = max(1, width - 2 * self.padding)
        inner_height = max(1, height - 2 * self.padding)

        self.canvas.coords(self.window_id, self.padding, self.padding)
        self.canvas.itemconfigure(
            self.window_id,
            width=inner_width,
            height=inner_height
        )

        self.canvas.tag_lower("card_shape")


class RoundedButton(tk.Frame):
    def __init__(
        self,
        parent,
        text,
        command=None,
        width=82,
        height=34,
        radius=9,
        bg="#eef2f7",
        hover_bg="#e2e8f0",
        fg="#0f172a",
        font=("Segoe UI", 9, "bold"),
        parent_bg="#ffffff",
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0
        )

        self.command = command
        self.width = width
        self.height = height
        self.radius = radius
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.text = text
        self.font = font
        self.parent_bg = parent_bg

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.canvas.bind("<Enter>", lambda event: self.draw(hover=True))
        self.canvas.bind("<Leave>", lambda event: self.draw(hover=False))
        self.canvas.bind("<Button-1>", self._clicked)

        self.draw()

    def _rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def draw(self, hover=False):
        self.canvas.delete("all")

        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())

        fill = self.hover_bg if hover else self.normal_bg

        self._rounded_rectangle(
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=fill,
            outline=fill
        )

        self.canvas.create_text(
            width / 2,
            height / 2,
            text=self.text,
            fill=self.fg,
            font=self.font
        )

    def _clicked(self, event=None):
        if self.command:
            self.command()

    def set_text(self, text):
        self.text = text
        self.draw()

    def set_style(self, style):
        if style == "accent":
            self.normal_bg = "#16a34a"
            self.hover_bg = "#166534"
            self.fg = "white"

        elif style == "danger":
            self.normal_bg = "#dc2626"
            self.hover_bg = "#991b1b"
            self.fg = "white"

        else:
            self.normal_bg = "#eef2f7"
            self.hover_bg = "#e2e8f0"
            self.fg = "#0f172a"

        self.draw()




class ModernStepperButton(tk.Frame):
    def __init__(
        self,
        parent,
        text,
        command=None,
        width=28,
        height=22,
        radius=9,
        bg="#eef2f7",
        hover_bg="#dcfce7",
        disabled_bg="#f1f5f9",
        fg="#0f172a",
        hover_fg="#166534",
        disabled_fg="#94a3b8",
        parent_bg="#fbfcfd",
        font=("Segoe UI", 8, "bold"),
    ):
        super().__init__(parent, width=width, height=height, bg=parent_bg, bd=0, highlightthickness=0)
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.radius = radius
        self.bg = bg
        self.hover_bg = hover_bg
        self.disabled_bg = disabled_bg
        self.fg = fg
        self.hover_fg = hover_fg
        self.disabled_fg = disabled_fg
        self.parent_bg = parent_bg
        self.font = font
        self.enabled = True
        self.hover = False

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.draw()

    def _rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def draw(self):
        self.canvas.delete("all")
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())

        if not self.enabled:
            fill = self.disabled_bg
            text_color = self.disabled_fg
            outline = self.disabled_bg
        elif self.hover:
            fill = self.hover_bg
            text_color = self.hover_fg
            outline = self.hover_bg
        else:
            fill = self.bg
            text_color = self.fg
            outline = self.bg

        self._rounded_rectangle(
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=fill,
            outline=outline,
        )
        self.canvas.create_text(
            width / 2,
            height / 2 - 1,
            text=self.text,
            fill=text_color,
            font=self.font,
        )

    def on_enter(self, event=None):
        if not self.enabled:
            return
        self.hover = True
        self.draw()

    def on_leave(self, event=None):
        if not self.enabled:
            return
        self.hover = False
        self.draw()

    def on_click(self, event=None):
        if self.enabled and self.command:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.hover = False
        self.canvas.configure(cursor="hand2" if self.enabled else "arrow")
        self.draw()


class SimpleToggle(tk.Frame):
    def __init__(
        self,
        parent,
        width=54,
        height=28,
        bg_on="#16a34a",
        bg_off="#d1d5db",
        knob="#ffffff",
        parent_bg="#ffffff",
        command=None,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
        )

        self.width = width
        self.height = height
        self.bg_on = bg_on
        self.bg_off = bg_off
        self.knob = knob
        self.parent_bg = parent_bg
        self.command = command
        self.is_on = True
        self._photo = None

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.toggle)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.draw()

    def _hex_to_rgb(self, color):
        color = color.lstrip("#")
        return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

    def _draw_high_res(self, width, height):
        width = max(int(width), int(self.width), 24)
        height = max(int(height), int(self.height), 16)

        scale = 4
        w = width * scale
        h = height * scale

        image = Image.new("RGB", (w, h), self._hex_to_rgb(self.parent_bg))
        draw = ImageDraw.Draw(image)

        pad = 2 * scale
        x1 = pad
        y1 = pad
        x2 = w - pad
        y2 = h - pad
        radius = int((y2 - y1) / 2)
        fill = self.bg_on if self.is_on else self.bg_off

        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=fill)

        knob_d = (y2 - y1) - 6 * scale
        knob_y1 = y1 + 3 * scale
        knob_y2 = knob_y1 + knob_d
        if self.is_on:
            knob_x1 = x1 + 3 * scale
        else:
            knob_x1 = x2 - knob_d - 3 * scale
        knob_x2 = knob_x1 + knob_d

        draw.ellipse((knob_x1, knob_y1 + scale, knob_x2, knob_y2 + scale), fill="#bfc5cc")
        draw.ellipse((knob_x1, knob_y1, knob_x2, knob_y2), fill=self.knob, outline=self.knob)

        image = image.resize((width, height), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")

    def draw_round_rect(self, x1, y1, x2, y2, radius, fill):
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=fill)
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=fill)
        self.canvas.create_oval(x1, y1, x1 + 2 * radius, y1 + 2 * radius, fill=fill, outline=fill)
        self.canvas.create_oval(x2 - 2 * radius, y1, x2, y1 + 2 * radius, fill=fill, outline=fill)
        self.canvas.create_oval(x2 - 2 * radius, y2 - 2 * radius, x2, y2, fill=fill, outline=fill)
        self.canvas.create_oval(x1, y2 - 2 * radius, x1 + 2 * radius, y2, fill=fill, outline=fill)

    def draw(self):
        self.canvas.delete("all")
        width = max(self.width, self.canvas.winfo_width())
        height = max(self.height, self.canvas.winfo_height())

        if PIL_AVAILABLE:
            self._draw_high_res(width, height)
            return

        pad = 2
        track_x1 = pad
        track_y1 = pad
        track_x2 = width - pad
        track_y2 = height - pad
        track_h = track_y2 - track_y1
        radius = track_h / 2
        fill = self.bg_on if self.is_on else self.bg_off

        self.draw_round_rect(track_x1, track_y1, track_x2, track_y2, radius, fill)

        knob_d = track_h - 6
        knob_y1 = track_y1 + 3
        knob_y2 = knob_y1 + knob_d
        if self.is_on:
            knob_x1 = track_x1 + 3
        else:
            knob_x1 = track_x2 - knob_d - 3
        knob_x2 = knob_x1 + knob_d

        self.canvas.create_oval(knob_x1, knob_y1, knob_x2, knob_y2, fill=self.knob, outline=self.knob)

    def toggle(self, event=None):
        self.is_on = not self.is_on
        self.draw()
        if self.command:
            self.command(self.is_on)


class SvgModeButton(tk.Frame):
    def __init__(
        self,
        parent,
        filename,
        command=None,
        button_size=74,
        icon_size=70,
        bg="#ffffff",
        border="#dfe5ec",
        selected_color="#16a34a",
        icon_color="#0f172a",
        disabled_color="#94a3b8",
        radius=16,
        enabled=True,
    ):
        super().__init__(
            parent,
            width=button_size,
            height=button_size,
            bg=bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )

        self.pack_propagate(False)
        self.grid_propagate(False)

        self.filename = filename
        self.command = command
        self.button_size = button_size
        self.icon_size = icon_size
        self.bg = bg
        self.border = border
        self.selected_color = selected_color
        self.icon_color = icon_color
        self.disabled_color = disabled_color
        self.radius = radius
        self.selected = False
        self.hover = False
        self.enabled = enabled

        self.image_normal = None
        self.image_selected = None
        self.image_disabled = None
        self.current_image = None
        self._bg_photo = None

        self.canvas = tk.Canvas(
            self,
            width=button_size,
            height=button_size,
            bg=bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.load_images()
        self.draw()

    def get_icon_path(self):
        path = os.path.join(app_dir(), self.filename)
        if os.path.exists(path):
            return path
        return None

    def load_images(self):
        path = self.get_icon_path()

        if path is None:
            self.canvas.create_text(
                self.button_size / 2,
                self.button_size / 2,
                text=f"Niet gevonden\n{self.filename}",
                fill="red",
                font=("Segoe UI", 8, "bold"),
                justify="center",
            )
            return

        try:
            self.image_normal = load_svg(path, self.icon_color, self.icon_size)
            self.image_selected = load_svg(path, self.selected_color, self.icon_size)
            self.image_disabled = load_svg(path, self.disabled_color, self.icon_size)
        except Exception:
            self.image_normal = None
            self.image_selected = None
            self.image_disabled = None

    def rounded_rectangle(self, x1, y1, x2, y2, radius, fill, outline, width=2):
        radius = max(0, min(radius, int((x2 - x1) / 2), int((y2 - y1) / 2)))
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        self.canvas.create_polygon(
            points,
            smooth=True,
            fill=fill,
            outline=outline,
            width=width,
        )

    def _hex_to_rgb(self, color):
        color = color.lstrip("#")
        return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

    def _draw_high_res_background(self, width, height, border_color, border_width):
        scale = 4
        w = width * scale
        h = height * scale

        image = Image.new("RGB", (w, h), self._hex_to_rgb(self.bg))
        draw = ImageDraw.Draw(image)

        pad = 2 * scale
        radius = int(self.radius * scale)
        draw.rounded_rectangle(
            (pad, pad, w - pad, h - pad),
            radius=radius,
            fill=self.bg,
            outline=border_color,
            width=border_width * scale,
        )

        image = image.resize((width, height), Image.Resampling.LANCZOS)
        self._bg_photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw")

    def draw(self):
        self.canvas.delete("all")

        width = max(int(self.button_size), int(self.canvas.winfo_width()), 32)
        height = max(int(self.button_size), int(self.canvas.winfo_height()), 32)

        active = self.enabled and (self.selected or self.hover)
        border_color = self.selected_color if active else self.border
        border_width = 3 if active else 2

        if PIL_AVAILABLE:
            self._draw_high_res_background(width, height, border_color, border_width)
        else:
            self.rounded_rectangle(
                2,
                2,
                width - 2,
                height - 2,
                self.radius,
                fill=self.bg,
                outline=border_color,
                width=border_width,
            )

        if not self.enabled:
            self.current_image = self.image_disabled
        elif active:
            self.current_image = self.image_selected
        else:
            self.current_image = self.image_normal

        if self.current_image is not None:
            self.canvas.create_image(width / 2, height / 2, image=self.current_image, anchor="center")

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.hover = False
            self.selected = False
            self.canvas.configure(cursor="arrow")
            self.configure(cursor="arrow")
        else:
            self.canvas.configure(cursor="hand2")
            self.configure(cursor="hand2")
        self.draw()

    def set_selected(self, selected):
        if not self.enabled and selected:
            return
        self.selected = selected
        self.draw()

    def on_enter(self, event=None):
        if not self.enabled:
            return
        self.hover = True
        self.draw()

    def on_leave(self, event=None):
        if not self.enabled:
            return
        self.hover = False
        self.draw()

    def on_click(self, event=None):
        if not self.enabled:
            return
        if self.command:
            self.command(self)


class ModernDropdown(tk.Frame):
    def __init__(
        self,
        parent,
        width=120,
        height=34,
        radius=9,
        bg="#ffffff",
        border="#dfe5ec",
        parent_bg="#ffffff",
        fg="#0f172a",
        muted="#64748b",
        font=("Segoe UI", 9),
        display_max_chars=12,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0
        )

        self.values = []
        self.selected = ""
        self.width = width
        self.height = height
        self.radius = radius
        self.bg = bg
        self.border = border
        self.parent_bg = parent_bg
        self.fg = fg
        self.muted = muted
        self.font = font
        self.display_max_chars = display_max_chars

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.canvas.bind("<Button-1>", self.show_menu)

        self.draw()

    def __setitem__(self, key, value):
        if key == "values":
            self.set_values(value)
        else:
            raise KeyError(key)

    def _rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def shorten_text(self, text, max_chars=18):
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 1] + "…"

    def draw(self):
        self.canvas.delete("all")

        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())

        self._rounded_rectangle(
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=self.border,
            outline=self.border
        )

        self._rounded_rectangle(
            2,
            2,
            width - 2,
            height - 2,
            max(1, self.radius - 1),
            fill=self.bg,
            outline=self.bg
        )

        display_text = self.selected if self.selected else "Kies COM"
        display_text = self.shorten_text(display_text, self.display_max_chars)

        self.canvas.create_text(
            10,
            height / 2,
            text=display_text,
            fill=self.fg if self.selected else self.muted,
            font=self.font,
            anchor="w"
        )

        self.canvas.create_text(
            width - 15,
            height / 2 + 1,
            text="▾",
            fill=self.muted,
            font=("Segoe UI", 10, "bold")
        )

    def set_values(self, values):
        self.values = list(values)

        if self.selected and self.selected not in self.values:
            self.selected = ""

        self.draw()

    def current(self, index):
        if not self.values:
            return

        if 0 <= index < len(self.values):
            self.selected = self.values[index]
            self.draw()

    def get(self):
        return self.selected

    def set(self, value):
        self.selected = value
        self.draw()

    def show_menu(self, event=None):
        if not self.values:
            return

        menu = tk.Menu(
            self,
            tearoff=0,
            bg="#ffffff",
            fg=self.fg,
            activebackground="#dcfce7",
            activeforeground="#166534",
            bd=1,
            relief="solid",
            font=self.font
        )

        for value in self.values:
            menu.add_command(
                label=value,
                command=lambda v=value: self.select_value(v)
            )

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def select_value(self, value):
        self.selected = value
        self.draw()


class UsbBtmsGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Gateway Monitor")

        icon_path = os.path.join(
            getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__))),
            "ev_europe_logo.ico"
        )
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.root.geometry("530x635")
        self.root.minsize(530, 635)

        self.serial_port = None
        self.running = False
        self.reader_thread = None
        self.queue = queue.Queue()

        self.bg = "#f7f9fb"
        self.card = "#ffffff"
        self.card_soft = "#fbfcfd"
        self.border = "#dfe5ec"

        self.green = "#16a34a"
        self.green_dark = "#166534"
        self.green_soft = "#dcfce7"
        self.blue_soft = "#65a9fc"

        self.orange = "#f59e0b"
        self.orange_soft = "#fff7ed"

        self.red = "#dc2626"
        self.red_soft = "#fee2e2"

        self.text = "#0f172a"
        self.muted = "#64748b"
        self.light_text = "#94a3b8"

        self.root.configure(bg=self.bg)

        self.value_vars = {}
        self.value_labels = {}
        self.current_manual_mode = 0
        self.manual_set_temp_c = 25
        self.manual_set_temp_user_changed = False
        self.manual_set_temp_buttons = []

        self.status_var = tk.StringVar(value="Niet verbonden")
        self.status_detail_var = tk.StringVar(value="")

        self.create_widgets()
        self.update_manual_set_temp_display()
        if self.auto_toggle.is_on:
            self.set_manual_set_temp_controls_enabled(False)

        self.refresh_ports()
        self.root.after(100, self.process_queue)

    def create_widgets(self):
        main = tk.Frame(self.root, bg=self.bg)
        main.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_header(main)

        content = tk.Frame(main, bg=self.bg)
        content.pack(fill="both", expand=True, pady=(4, 0))

        content.columnconfigure(0, weight=0)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(0, weight=0)
        content.rowconfigure(1, weight=0)

        self.create_control_mode_group(
            content,
            row=0,
            col=0,
            height=100,
            colspan=2
        )

        self.create_group(
            content,
            title="BMS data",
            fields=[
                ("Gemiddelde temp", "BMS_AVG", "°C"),
                ("Min temp", "BMS_MIN", "°C"),
                ("Max temp", "BMS_MAX", "°C"),
                ("Pack spanning", "PACK_MV", "V"),
                ("Aantal berichten", "BMS_RX", ""),
            ],
            row=1,
            col=0
        )

        self.create_group(
            content,
            title="Berichten naar BTMS",
            fields=[
                ("Mode", "TX_MODE", ""),
                ("Set temperatuur", "TX_SET", "°C"),
                ("HV spanning", "TX_VOLT", "V"),
                ("Aantal berichten", "BTMS_TX", ""),
            ],
            row=1,
            col=1
        )

        self.create_group(
            content,
            title="Berichten van BTMS",
            fields=[
                ("Mode", "RX_MODE", ""),
                ("Uitlaattemp", "TOUT", "°C"),
                ("Inlaattemp", "TIN", "°C"),
                ("Buitentemp", "TAMB", "°C"),
                ("Vraagvermogen", "PDEM_X10", "kW"),
                ("Aantal berichten", "BTMS_RX", ""),
            ],
            row=2,
            col=0,
            height=210
        )

        self.create_error_and_raw_group(content, row=2, col=1, height=210)

    def create_header(self, parent):
        header_card = RoundedCard(
            parent,
            bg=self.card,
            border=self.border,
            parent_bg=self.bg,
            radius=14,
            padding=0,
            height=86
        )
        header_card.pack(fill="x")
        header_card.pack_propagate(False)
        header_card.grid_propagate(False)

        header = header_card.inner

        inner = tk.Frame(header, bg=self.card)
        inner.pack(fill="both", expand=True, padx=10, pady=6)

        left = tk.Frame(inner, bg=self.card)
        left.pack(side="left", fill="both", expand=True)

        title_line = tk.Frame(left, bg=self.card)
        title_line.pack(fill="x")

        tk.Label(
            title_line,
            text="Gateway Monitor",
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 15, "bold")
        ).pack(side="left")

        status_line = tk.Frame(left, bg=self.card)
        status_line.pack(fill="x", pady=(2, 0))

        self.status_dot = tk.Label(
            status_line,
            text="●",
            bg=self.card,
            fg=self.light_text,
            font=("Segoe UI", 10, "bold")
        )
        self.status_dot.pack(side="left", padx=(0, 6))

        tk.Label(
            status_line,
            textvariable=self.status_var,
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        controls = tk.Frame(inner, bg=self.card)
        controls.pack(side="right", pady=(8, 0), anchor="e")

        self.port_combo = ModernDropdown(
            controls,
            width=120,
            height=34,
            radius=9,
            bg="#ffffff",
            border=self.border,
            parent_bg=self.card,
            fg=self.text,
            muted=self.muted,
            font=("Segoe UI", 9),
            display_max_chars=12
        )
        self.port_combo.grid(row=0, column=0, padx=(0, 6))

        self.refresh_button = RoundedButton(
            controls,
            text="Refresh",
            command=self.refresh_ports,
            width=74,
            height=34,
            radius=9,
            bg="#eef2f7",
            hover_bg="#e2e8f0",
            fg=self.text,
            parent_bg=self.card
        )
        self.refresh_button.grid(row=0, column=1, padx=(0, 6))

        self.connect_button = RoundedButton(
            controls,
            text="Verbinden",
            command=self.toggle_connection,
            width=92,
            height=34,
            radius=9,
            bg=self.green,
            hover_bg=self.green_dark,
            fg="white",
            parent_bg=self.card
        )
        self.connect_button.grid(row=0, column=2)

    def create_control_mode_group(self, parent, row, col, height=100, colspan=2):
        card_width = 260 * colspan + 4 * (colspan - 1)

        outer_card = RoundedCard(
            parent,
            bg=self.card,
            border=self.border,
            parent_bg=self.bg,
            radius=14,
            padding=0,
            width=card_width,
            height=height
        )
        outer_card.grid(row=row, column=col, columnspan=colspan, sticky="nw", padx=2, pady=2)
        outer_card.grid_propagate(False)
        outer_card.pack_propagate(False)

        outer = outer_card.inner

        layout = tk.Frame(outer, bg=self.card)
        layout.pack(fill="both", expand=True, padx=10, pady=8)

        title_frame = tk.Frame(layout, bg=self.card, width=145)
        title_frame.pack(side="left", fill="y", padx=(0, 8))
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="Besturingsmodus",
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 0))

        toggle_area = tk.Frame(title_frame, bg=self.card)
        toggle_area.pack(fill="both", expand=True)

        self.auto_toggle = SimpleToggle(
            toggle_area,
            width=54,
            height=28,
            bg_on=self.blue_soft,
            bg_off=self.green,
            parent_bg=self.card,
            command=self.set_control_mode_auto,
        )
        self.auto_toggle.pack(anchor="center", pady=(10, 0))

        self.control_mode_text_var = tk.StringVar(value="Automatisch")
        tk.Label(
            toggle_area,
            textvariable=self.control_mode_text_var,
            bg=self.card,
            fg=self.muted,
            font=("Segoe UI", 8, "bold"),
            anchor="center"
        ).pack(anchor="center", pady=(3, 0))

        icon_frame = tk.Frame(layout, bg=self.card)
        icon_frame.pack(side="left", fill="both", expand=True)

        icon_files = [
            "power.svg",
            "snow.svg",
            "fire.svg",
            "recycle.svg",
        ]

        for i in range(4):
            icon_frame.grid_columnconfigure(i, weight=1, uniform="icons")
        icon_frame.grid_rowconfigure(0, weight=1)

        self.mode_buttons = []

        for index, filename in enumerate(icon_files):
            button = SvgModeButton(
                icon_frame,
                filename=filename,
                command=self.select_mode_button,
                button_size=74,
                icon_size=40,
                bg=self.card,
                border=self.border,
                selected_color=self.green,
                icon_color=self.text,
                disabled_color=self.light_text,
                radius=16,
                enabled=False,
            )
            button.mode_code = index
            button.grid(row=0, column=index, sticky="nsew", padx=4, pady=4)
            self.mode_buttons.append(button)

        self.set_control_mode_auto(True)

    def set_control_mode_auto(self, is_auto):
        if is_auto:
            self.control_mode_text_var.set("Automatisch")
            for button in self.mode_buttons:
                button.set_enabled(False)
            self.manual_set_temp_user_changed = False
            self.set_manual_set_temp_controls_enabled(False)
            self.send_btms_control_auto()
        else:
            self.control_mode_text_var.set("Handmatig")
            for button in self.mode_buttons:
                button.set_enabled(True)
            self.set_manual_set_temp_controls_enabled(True)
            self.update_manual_set_temp_display()
            if self.mode_buttons:
                self.select_mode_button(self.mode_buttons[0])

    def select_mode_button(self, clicked_button):
        for button in self.mode_buttons:
            button.set_selected(button is clicked_button)

        self.current_manual_mode = getattr(clicked_button, "mode_code", 0)
        if not self.auto_toggle.is_on:
            self.send_btms_control_manual(self.current_manual_mode)

    def send_serial_line(self, line):
        if not self.running or self.serial_port is None:
            return

        try:
            self.serial_port.write((line + "\n").encode("ascii"))
        except Exception as exc:
            self.set_status(
                title="Seriële schrijffout",
                detail=str(exc),
                state="error"
            )

    def send_btms_control_auto(self):
        self.send_serial_line("CTRL=AUTO")

    def send_btms_control_manual(self, mode):
        set_temp = int(self.manual_set_temp_c)
        self.send_serial_line(f"CTRL=MANUAL;MODE={int(mode)};SET={set_temp}")

    def create_group(self, parent, title, fields, row, col, height=210):
        outer_card = RoundedCard(
            parent,
            bg=self.card,
            border=self.border,
            parent_bg=self.bg,
            radius=14,
            padding=0,
            width=260,
            height=height
        )
        outer_card.grid(row=row, column=col, sticky="nw", padx=2, pady=2)
        outer_card.grid_propagate(False)
        outer_card.pack_propagate(False)

        outer = outer_card.inner

        header = tk.Frame(outer, bg=self.card)
        header.pack(fill="x", padx=8, pady=(6, 3))

        tk.Label(
            header,
            text=title,
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        grid = tk.Frame(outer, bg=self.card)
        grid.pack(anchor="w", padx=6, pady=(0, 5))

        for i, (label, key, unit) in enumerate(fields):
            if key == "TX_SET":
                self.create_temperature_stepper_card(grid, label, key, unit, i)
            else:
                self.create_value_card(grid, label, key, unit, i)

        grid.columnconfigure(0, weight=0)
        grid.columnconfigure(1, weight=0)

    def create_error_and_raw_group(self, parent, row, col, height=250):
        outer_card = RoundedCard(
            parent,
            bg=self.card,
            border=self.border,
            parent_bg=self.bg,
            radius=14,
            padding=0,
            width=260,
            height=height
        )
        outer_card.grid(row=row, column=col, sticky="nw", padx=2, pady=2)
        outer_card.grid_propagate(False)
        outer_card.pack_propagate(False)

        outer = outer_card.inner

        header = tk.Frame(outer, bg=self.card)
        header.pack(fill="x", padx=8, pady=(6, 3))

        tk.Label(
            header,
            text="Foutstatus",
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        grid = tk.Frame(outer, bg=self.card)
        grid.pack(anchor="w", padx=6, pady=(0, 3))

        self.create_value_card(grid, "Foutcode", "ERR", "", 0)
        self.create_value_card(grid, "Foutniveau", "ERRLVL", "", 1)
        self.create_value_card(grid, "Foutomschrijving", "ERR_TEXT", "", 2, colspan=2)

        grid.columnconfigure(0, weight=0)
        grid.columnconfigure(1, weight=0)


    def create_temperature_stepper_card(self, parent, label, key, unit, index):
        row = index // 2
        col = index % 2

        card = RoundedCard(
            parent,
            bg=self.card_soft,
            border=self.border,
            parent_bg=self.card,
            radius=12,
            padding=0,
            height=62,
            width=120
        )
        card.grid(row=row, column=col, sticky="w", padx=1, pady=2)
        card.grid_propagate(False)
        card.pack_propagate(False)

        inner = card.inner

        tk.Label(
            inner,
            text=label,
            bg=self.card_soft,
            fg=self.muted,
            font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).pack(fill="x", padx=8, pady=(4, 0))

        body = tk.Frame(inner, bg=self.card_soft)
        body.pack(fill="x", padx=7, pady=(2, 0))

        var = tk.StringVar(value="-")
        self.value_vars[key] = (var, unit)

        value_label = tk.Label(
            body,
            textvariable=var,
            bg=self.card_soft,
            fg=self.green_dark,
            font=("Segoe UI", 16, "bold"),
            anchor="w"
        )
        value_label.pack(side="left", fill="x", expand=True)
        self.value_labels[key] = value_label

        arrows = tk.Frame(body, bg=self.card_soft)
        arrows.pack(side="right", padx=(3, 0))

        up_button = ModernStepperButton(
            arrows,
            text="▲",
            command=lambda: self.change_manual_set_temp(1),
            width=15,
            height=15,
            radius=9,
            bg="#e8eef5",
            hover_bg=self.green_soft,
            fg=self.text,
            hover_fg=self.green_dark,
            parent_bg=self.card_soft,
            font=("Segoe UI", 7, "bold"),
        )
        up_button.pack(fill="x", pady=(0, 2))

        down_button = ModernStepperButton(
            arrows,
            text="▼",
            command=lambda: self.change_manual_set_temp(-1),
            width=15,
            height=15,
            radius=9,
            bg="#e8eef5",
            hover_bg=self.green_soft,
            fg=self.text,
            hover_fg=self.green_dark,
            parent_bg=self.card_soft,
            font=("Segoe UI", 7, "bold"),
        )
        down_button.pack(fill="x")

        self.manual_set_temp_buttons = [up_button, down_button]
        self.set_manual_set_temp_controls_enabled(False)

    def set_manual_set_temp_controls_enabled(self, enabled):
        buttons = getattr(self, "manual_set_temp_buttons", [])
        for button in buttons:
            try:
                button.set_enabled(enabled)
            except Exception:
                pass

    def clamp_manual_set_temp(self, value):
        return max(MANUAL_SET_TEMP_MIN, min(MANUAL_SET_TEMP_MAX, int(value)))

    def update_manual_set_temp_display(self):
        if "TX_SET" not in self.value_vars:
            return

        var, _ = self.value_vars["TX_SET"]
        var.set(f"{int(self.manual_set_temp_c)} °C")

    def change_manual_set_temp(self, delta):
        if self.auto_toggle.is_on:
            return

        self.manual_set_temp_c = self.clamp_manual_set_temp(self.manual_set_temp_c + delta)
        self.manual_set_temp_user_changed = True
        self.update_manual_set_temp_display()
        self.send_btms_control_manual(self.current_manual_mode)


    def create_value_card(self, parent, label, key, unit, index, colspan=1):
        row = index // 2
        col = index % 2

        if colspan == 2:
            row = 1
            col = 0

        default_width = 120

        card = RoundedCard(
            parent,
            bg=self.card_soft,
            border=self.border,
            parent_bg=self.card,
            radius=10,
            padding=0,
            height=54,
            width=default_width
        )

        sticky = "nsew" if colspan == 2 else "w"
        card.grid(
            row=row,
            column=col,
            columnspan=colspan,
            sticky=sticky,
            padx=1,
            pady=2
        )
        card.grid_propagate(False)
        card.pack_propagate(False)

        inner = card.inner

        tk.Label(
            inner,
            text=label,
            bg=self.card_soft,
            fg=self.muted,
            font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).pack(fill="x", padx=8, pady=(3, 0))

        var = tk.StringVar(value="-")
        self.value_vars[key] = (var, unit)

        value_label = tk.Label(
            inner,
            textvariable=var,
            bg=self.card_soft,
            fg=self.green_dark,
            font=("Segoe UI", 15, "bold"),
            anchor="w"
        )
        value_label.pack(fill="x", padx=8, pady=(0, 1))

        self.value_labels[key] = value_label

    def refresh_ports(self):
        ports = list(serial.tools.list_ports.comports())
        values = []

        for port in ports:
            description = port.description
            description = re.sub(r"\s*\(COM\d+\)\s*$", "", description)
            
            if "Serieel USB-apparaat" in description:
                description = "STM32 BTMS Gateway"
            values.append(f"{port.device} - {description}")

        self.port_combo["values"] = values

        if values:
            current = self.port_combo.get()
            if not current or current not in values:
                self.port_combo.current(0)
        else:
            self.port_combo.set("")

    def toggle_connection(self):
        if self.running:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        selected = self.port_combo.get()

        if not selected:
            messagebox.showerror("Geen poort", "Selecteer eerst een COM-poort.")
            return

        port = selected.split(" - ")[0].strip()

        try:
            self.serial_port = serial.Serial(port, BAUDRATE, timeout=0.2)
        except Exception as exc:
            messagebox.showerror("Verbindingsfout", str(exc))
            self.set_status(
                title="Verbinding mislukt",
                detail=str(exc),
                state="error"
            )
            return

        self.running = True
        self.connect_button.set_text("Verbreken")
        self.connect_button.set_style("danger")

        self.set_status(
            title=f"Verbonden met {port}",
            detail="",
            state="connected"
        )

        self.reader_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.reader_thread.start()

        if self.auto_toggle.is_on:
            self.send_btms_control_auto()
        else:
            self.send_btms_control_manual(self.current_manual_mode)

    def disconnect(self):
        self.running = False

        if self.serial_port is not None:
            try:
                self.serial_port.close()
            except Exception:
                pass

        self.serial_port = None
        self.connect_button.set_text("Verbinden")
        self.connect_button.set_style("accent")

        self.set_status(
            title="Niet verbonden",
            detail="Selecteer een COM-poort.",
            state="offline"
        )

    def read_serial_loop(self):
        while self.running:
            try:
                raw = self.serial_port.readline()

                if not raw:
                    continue

                line = raw.decode(errors="ignore").strip()

                if line:
                    self.queue.put(line)

            except Exception as exc:
                if self.running:
                    self.queue.put(f"__ERROR__={exc}")
                break

    def process_queue(self):
        while not self.queue.empty():
            line = self.queue.get()

            if line.startswith("__ERROR__="):
                error_text = line.replace("__ERROR__=", "")
                self.set_status(
                    title="Seriële leesfout",
                    detail=error_text,
                    state="error"
                )
                continue

            data = parse_line(line)
            self.update_values(data)

        self.root.after(100, self.process_queue)

    def update_values(self, data):
        for key, (var, unit) in self.value_vars.items():
            if key == "ERR_TEXT":
                continue

            if key not in data:
                continue

            value = data[key]

            if key == "TX_SET":
                try:
                    tx_set_temp = int(float(value))
                    if self.auto_toggle.is_on and not self.manual_set_temp_user_changed:
                        self.manual_set_temp_c = self.clamp_manual_set_temp(tx_set_temp)
                    if self.auto_toggle.is_on:
                        var.set(f"{tx_set_temp} °C")
                    else:
                        self.update_manual_set_temp_display()
                except Exception:
                    var.set(f"{value} {unit}" if unit else value)

            elif key == "PACK_MV":
                try:
                    voltage = int(value) / 1000
                    var.set(f"{voltage:.2f} V")
                except Exception:
                    var.set(f"{value} mV")

            elif key == "PDEM_X10":
                try:
                    power = int(value) / 10
                    var.set(f"{power:.1f} kW")
                except Exception:
                    var.set(value)

            elif key in ("TX_MODE", "RX_MODE"):
                mode_text = mode_to_text(value)
                var.set(mode_text)
                label = self.value_labels.get(key)
                if label is not None:
                    if mode_text == "Self recycling":
                        label.configure(font=("Segoe UI", 11, "bold"))
                    else:
                        label.configure(font=("Segoe UI", 15, "bold"))

            elif key in ("TX_RELAY", "RX_RELAY"):
                var.set(relay_to_text(value))

            elif key == "ERRLVL":
                var.set(error_level_to_text(value))

            elif unit:
                var.set(f"{value} {unit}")

            else:
                var.set(value)

        self.update_error_status(data)

    def update_error_status(self, data):
        err = data.get("ERR")
        errlvl = data.get("ERRLVL")

        if err is None and errlvl is None:
            return

        try:
            err_int = int(err)
        except Exception:
            err_int = None

        try:
            lvl_int = int(errlvl)
        except Exception:
            lvl_int = None

        err_text_var, _ = self.value_vars["ERR_TEXT"]

        if err_int is None:
            err_text_var.set("-")
        else:
            err_text_var.set(error_code_to_text(err_int))

        if err_int == 0 and (lvl_int == 0 or lvl_int is None):
            self.set_status(
                title="Verbonden",
                detail="",
                state="connected"
            )
            self.set_error_cards(ok=True)

        else:
            level_text = error_level_to_text(lvl_int) if lvl_int is not None else "-"
            error_text = error_code_to_text(err_int) if err_int is not None else "Onbekende fout"

            self.set_status(
                title=f"BTMS fout actief: {err_int}",
                detail=f"{level_text} - {error_text}",
                state="error"
            )
            self.set_error_cards(ok=False)

    def set_error_cards(self, ok=True):
        keys = ["ERR", "ERRLVL", "ERR_TEXT"]

        for key in keys:
            label = self.value_labels.get(key)
            if label is None:
                continue

            if ok:
                label.configure(fg=self.green_dark)
            else:
                label.configure(fg=self.red)

    def set_status(self, title, detail="", state="offline"):
        self.status_var.set(title)

        if state == "connected":
            self.status_dot.configure(fg=self.green)

        elif state == "ready":
            self.status_dot.configure(fg=self.orange)

        elif state == "warning":
            self.status_dot.configure(fg=self.orange)

        elif state == "error":
            self.status_dot.configure(fg=self.red)

        else:
            self.status_dot.configure(fg=self.light_text)

    def on_close(self):
        self.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = UsbBtmsGui(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
