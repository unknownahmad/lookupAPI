# ==========================================
# FINAL CODE
# ==========================================

import customtkinter as ctk

# Shared dark developer-tool colour palette
BG_MAIN = "#0D1117"
BG_SIDEBAR = "#11161F"
BG_CARD = "#161B26"
BG_SURFACE = "#1E2634"
BG_SURFACE_HOVER = "#263144"
BG_CODE = "#0A0E14"

BORDER_COLOR = "#273142"
BORDER_SUBTLE = "#1E2736"

ACCENT_PRIMARY = "#3B82F6"
ACCENT_HOVER = "#2563EB"
ACCENT_SECONDARY = "#38BDF8"

TEXT_MAIN = "#F1F5F9"
TEXT_SECONDARY = "#CBD5E1"
TEXT_MUTED = "#8B9BB4"

COLOR_SUCCESS = "#22C55E"
COLOR_SUCCESS_TEXT = "#052E16"
COLOR_WARNING = "#F59E0B"
COLOR_WARNING_TEXT = "#1C1917"
COLOR_ERROR = "#EF4444"
COLOR_ERROR_HOVER = "#DC2626"
COLOR_INFO_TEXT = "#082F49"

METHOD_COLORS = {
    "GET": "#0284C7",
    "POST": "#15803D",
    "PUT": "#B45309",
    "DELETE": "#B91C1C",
    "PATCH": "#4F46E5",
}

# Typography & layout tokens
FONT_FAMILY = "Helvetica Neue"
MONO_FONT = "Menlo"

RADIUS_PANEL = 8
RADIUS_CONTROL = 6
RADIUS_BADGE = 4

PAD_PAGE_X = 24
BTN_HEIGHT = 32
BTN_HEIGHT_SM = 26
INPUT_HEIGHT = 34


def font_ui(size=12, weight="normal"):
    """Create a consistent UI sans-serif font."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def font_mono(size=11, weight="normal"):
    """Create a consistent monospace font for URLs, JSON payloads, and timestamps."""
    return ctk.CTkFont(family=MONO_FONT, size=size, weight=weight)
