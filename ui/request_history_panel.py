# ==========================================
# FINAL CODE
# ==========================================

from functools import partial
import customtkinter as ctk

from functions.request_history import HISTORY_FILE, load_request_history
from ui.menu import wrap_long_text
from ui.theme import (
    ACCENT_PRIMARY, ACCENT_SECONDARY, BG_CARD, BG_SURFACE, BG_SURFACE_HOVER,
    BORDER_COLOR, BTN_HEIGHT_SM, COLOR_ERROR, COLOR_SUCCESS,
    COLOR_SUCCESS_TEXT, COLOR_WARNING, COLOR_WARNING_TEXT, METHOD_COLORS,
    RADIUS_BADGE, RADIUS_CONTROL, TEXT_MAIN, TEXT_MUTED, font_mono, font_ui,
)


def format_history_status(entry):
    """Return display label and colours for a stored request history status."""
    safe_entry = entry if isinstance(entry, dict) else {}
    status_code = safe_entry.get("status_code")
    success = bool(safe_entry.get("success", False))
    valid_status = isinstance(status_code, int) and not isinstance(status_code, bool)

    if not valid_status:
        return "  Failed  ", COLOR_ERROR, TEXT_MAIN
    if success:
        return f"  HTTP {status_code}  ", COLOR_SUCCESS, COLOR_SUCCESS_TEXT
    if status_code == 429:
        return "  HTTP 429  ", COLOR_WARNING, COLOR_WARNING_TEXT
    return f"  HTTP {status_code}  ", COLOR_ERROR, TEXT_MAIN


def render_history_row(parent, entry, avail_w):
    """Render one recorded API test request card."""
    method = str(entry.get("method") or "GET").upper()
    api_name = str(entry.get("api_name") or "Unknown API")
    url = str(entry.get("url") or "Not available")
    timestamp = str(entry.get("timestamp") or "Unknown time")
    elapsed = entry.get("response_time_ms")
    valid_time = isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool)
    time_txt = f"{elapsed} ms" if valid_time else "—"
    outcome_txt = "Succeeded" if entry.get("success") else "Failed"
    outcome_color = COLOR_SUCCESS if entry.get("success") else COLOR_ERROR
    badge_text, badge_bg, badge_fg = format_history_status(entry)

    row = ctk.CTkFrame(parent, fg_color=BG_SURFACE, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    row.pack(padx=10, pady=3, fill="x")

    top = ctk.CTkFrame(row, fg_color="transparent")
    top.pack(padx=10, pady=(5, 2), fill="x")
    ctk.CTkLabel(
        top, text=method, width=54, height=20, corner_radius=RADIUS_BADGE, anchor="center",
        fg_color=METHOD_COLORS.get(method, ACCENT_PRIMARY), text_color=TEXT_MAIN, font=font_ui(10, "bold"),
    ).pack(side="left", padx=(0, 8))

    ctk.CTkLabel(top, text=api_name[:46], height=20, text_color=TEXT_MAIN, anchor="w", font=font_ui(12, "bold")).pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(top, text=time_txt, height=20, text_color=TEXT_MUTED, font=font_mono(11)).pack(side="right", padx=(8, 0))
    ctk.CTkLabel(top, text=badge_text, height=20, fg_color=badge_bg, text_color=badge_fg, corner_radius=RADIUS_BADGE, font=font_ui(10, "bold")).pack(side="right")

    url_chars = max(30, int(max(240, avail_w - 40) / 7.2))
    ctk.CTkLabel(
        row, text=wrap_long_text(url, url_chars), height=18, text_color=ACCENT_SECONDARY,
        wraplength=max(240, avail_w - 40), justify="left", anchor="w", font=font_mono(11),
    ).pack(padx=10, pady=(0, 1), fill="x")

    meta = ctk.CTkFrame(row, fg_color="transparent")
    meta.pack(padx=10, pady=(0, 5), fill="x")
    ctk.CTkLabel(meta, text=timestamp, height=16, text_color=TEXT_MUTED, font=font_mono(10)).pack(side="left")
    ctk.CTkLabel(meta, text=outcome_txt, height=16, text_color=outcome_color, font=font_ui(10, "bold")).pack(side="right")


def render_request_history_panel(details_frame, status_label, history_file=HISTORY_FILE):
    """Display previously executed API test requests inside the details panel."""
    for child in details_frame.winfo_children():
        child.destroy()
    if hasattr(details_frame, "_parent_canvas"):
        details_frame._parent_canvas.yview_moveto(0)

    details_frame.update_idletasks()
    panel_w = details_frame.winfo_width()
    avail_w = max(320, (panel_w if panel_w > 200 else 540) - 68)

    entries = load_request_history(file_path=history_file)

    header_card = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    header_card.pack(padx=6, pady=(4, 3), fill="x")
    top_row = ctk.CTkFrame(header_card, fg_color="transparent")
    top_row.pack(padx=12, pady=(7, 2), fill="x")
    ctk.CTkLabel(top_row, text="TEST REQUEST HISTORY", text_color=ACCENT_SECONDARY, font=font_ui(10, "bold")).pack(side="left")
    ctk.CTkButton(
        top_row, text="Refresh", width=78, height=BTN_HEIGHT_SM, corner_radius=RADIUS_CONTROL,
        fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER, border_width=1, border_color=BORDER_COLOR,
        text_color=TEXT_MAIN, font=font_ui(11),
        command=partial(render_request_history_panel, details_frame, status_label, history_file),
    ).pack(side="right")

    ctk.CTkLabel(
        header_card, text=f"{len(entries)} recorded API test request(s) · Stored in data/test_request_history.json (no headers or credentials).",
        text_color=TEXT_MUTED, wraplength=avail_w, justify="left", anchor="w", font=font_ui(11),
    ).pack(padx=12, pady=(0, 7), fill="x")

    list_card = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    list_card.pack(padx=6, pady=(3, 6), fill="x")

    if len(entries) == 0:
        ctk.CTkLabel(
            list_card, text="No test requests recorded yet. Select an API on the left and click 'Send Request' to see history here.",
            text_color=TEXT_MUTED, wraplength=avail_w, justify="left", anchor="w", font=font_ui(12),
        ).pack(padx=14, pady=12, fill="x")
        status_label.configure(text="Request history is empty.", text_color=TEXT_MUTED)
        return entries

    ctk.CTkFrame(list_card, height=3, fg_color="transparent").pack(fill="x")
    for entry in reversed(entries):
        render_history_row(list_card, entry, avail_w)
    ctk.CTkFrame(list_card, height=3, fg_color="transparent").pack(fill="x")

    status_label.configure(text=f"Showing {len(entries)} recorded test request(s) (newest first).", text_color=ACCENT_SECONDARY)
    return entries
