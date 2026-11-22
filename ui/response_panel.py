# ==========================================
# FINAL CODE
# ==========================================

from functools import partial
import customtkinter as ctk

from ui.theme import (
    ACCENT_PRIMARY, ACCENT_SECONDARY, BG_CARD, BG_CODE, BG_SURFACE,
    BG_SURFACE_HOVER, BORDER_COLOR, BORDER_SUBTLE, BTN_HEIGHT_SM, COLOR_ERROR,
    COLOR_SUCCESS, COLOR_SUCCESS_TEXT, COLOR_WARNING, COLOR_WARNING_TEXT,
    RADIUS_BADGE, RADIUS_CONTROL, TEXT_MAIN, TEXT_MUTED, font_mono, font_ui,
)

DEFAULT_RESPONSE_PLACEHOLDER = "Click 'Send Request' to execute a request and inspect the formatted response here."


def handle_copy_response(tester_state, ui_refs):
    """Copy the current formatted response body to the system clipboard."""
    text_to_copy = tester_state.get("last_body") or ""
    if not text_to_copy:
        ui_refs["status_label"].configure(text="Nothing to copy — send a request first.", text_color=COLOR_WARNING)
        return False

    root = ui_refs["response_box"].winfo_toplevel()
    root.clipboard_clear()
    root.clipboard_append(text_to_copy)
    root.update_idletasks()
    ui_refs["status_label"].configure(text="Response copied to clipboard.", text_color=COLOR_SUCCESS)
    return True


def handle_clear_response(tester_state, ui_refs):
    """Reset the response panel back to its clean initial state."""
    tester_state["last_result"] = None
    tester_state["last_body"] = ""

    ui_refs["status_badge"].configure(text="  Ready  ", fg_color=BG_SURFACE, text_color=TEXT_MUTED)
    ui_refs["time_label"].configure(text="Time: —")
    ui_refs["format_label"].configure(text="", fg_color="transparent", text_color=TEXT_MUTED)
    ui_refs["error_label"].configure(text="", text_color=TEXT_MUTED)

    resp_box = ui_refs["response_box"]
    resp_box.configure(state="normal")
    resp_box.delete("1.0", "end")
    resp_box.insert("1.0", DEFAULT_RESPONSE_PLACEHOLDER)
    resp_box.configure(state="disabled")

    ui_refs["status_label"].configure(text="Response cleared.", text_color=TEXT_MUTED)


def update_response_card(result, tester_state, ui_refs):
    """Render status code, timing, format indicator, error banner, and scrollable body."""
    ui_refs["send_btn"].configure(state="normal", text="Send Request")
    method = str(result.get("method") or tester_state.get("method") or "GET").upper()
    status_code = result.get("status_code")
    reason = result.get("reason") or ""
    elapsed_ms = result.get("response_time_ms", 0.0)
    error_msg = result.get("error") or ""
    body_text = result.get("body") or ""

    ui_refs["time_label"].configure(text=f"Time: {elapsed_ms} ms")

    if status_code is not None:
        status_text = f"HTTP {status_code} {reason}".strip()
        if result.get("ok"):
            badge_bg, badge_fg = COLOR_SUCCESS, COLOR_SUCCESS_TEXT
        elif result.get("rate_limited"):
            badge_bg, badge_fg = COLOR_WARNING, COLOR_WARNING_TEXT
        else:
            badge_bg, badge_fg = COLOR_ERROR, TEXT_MAIN
        ui_refs["status_badge"].configure(text=f"  {status_text}  ", fg_color=badge_bg, text_color=badge_fg)
    else:
        fail_label = "Invalid JSON" if reason == "Invalid JSON" else "Request Failed"
        ui_refs["status_badge"].configure(text=f"  {fail_label}  ", fg_color=COLOR_ERROR, text_color=TEXT_MAIN)

    if body_text:
        if result.get("is_json"):
            ui_refs["format_label"].configure(text="  JSON  ", fg_color=ACCENT_PRIMARY, text_color=TEXT_MAIN)
        else:
            ui_refs["format_label"].configure(text="  Raw Text  ", fg_color=BG_SURFACE, text_color=TEXT_MUTED)
    else:
        ui_refs["format_label"].configure(text="", fg_color="transparent", text_color=TEXT_MUTED)

    if error_msg:
        err_color = COLOR_WARNING if (result.get("ok") or result.get("rate_limited")) else COLOR_ERROR
        ui_refs["error_label"].configure(text=error_msg, text_color=err_color)
    else:
        ui_refs["error_label"].configure(text="", text_color=TEXT_MUTED)

    display_body = body_text if body_text else (error_msg or "(Empty response body)")
    tester_state["last_body"] = body_text if body_text else error_msg

    resp_box = ui_refs["response_box"]
    resp_box.configure(state="normal")
    resp_box.delete("1.0", "end")
    resp_box.insert("1.0", display_body)
    resp_box.configure(state="disabled")

    if result.get("ok"):
        ui_refs["status_label"].configure(text=f"{method} request succeeded: HTTP {status_code} in {elapsed_ms} ms.", text_color=COLOR_SUCCESS)
    elif result.get("rate_limited"):
        ui_refs["status_label"].configure(text="Rate limit reached (HTTP 429). Wait before retrying.", text_color=COLOR_WARNING)
    else:
        ui_refs["status_label"].configure(text=error_msg[:95] or "Request failed.", text_color=COLOR_ERROR)


def build_response_card(details_frame, tester_state, ui_refs, avail_w):
    """Build the scrollable Response card with status, format badge, Copy, and Clear controls."""
    resp_card = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    resp_card.pack(padx=6, pady=(4, 8), fill="x")

    resp_top = ctk.CTkFrame(resp_card, fg_color="transparent")
    resp_top.pack(padx=14, pady=(10, 6), fill="x")
    ctk.CTkLabel(resp_top, text="RESPONSE OUTPUT", text_color=ACCENT_SECONDARY, font=font_ui(10, "bold")).pack(side="left")

    format_label = ctk.CTkLabel(resp_top, text="", corner_radius=RADIUS_BADGE, fg_color="transparent", text_color=TEXT_MUTED, font=font_ui(10, "bold"))
    format_label.pack(side="right", padx=(6, 0))
    time_label = ctk.CTkLabel(resp_top, text="Time: —", text_color=TEXT_MUTED, font=font_mono(11))
    time_label.pack(side="right", padx=(8, 0))
    status_badge = ctk.CTkLabel(resp_top, text="  Ready  ", fg_color=BG_SURFACE, text_color=TEXT_MUTED, corner_radius=RADIUS_BADGE, font=font_ui(11, "bold"))
    status_badge.pack(side="right")

    ctk.CTkFrame(resp_card, height=1, fg_color=BORDER_SUBTLE).pack(padx=12, pady=(0, 8), fill="x")

    actions_row = ctk.CTkFrame(resp_card, fg_color="transparent")
    actions_row.pack(padx=12, pady=(0, 6), fill="x")
    copy_btn = ctk.CTkButton(
        actions_row, text="Copy Response", width=114, height=BTN_HEIGHT_SM, corner_radius=RADIUS_CONTROL,
        fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER, border_width=1, border_color=BORDER_COLOR,
        text_color=TEXT_MAIN, font=font_ui(11, "bold"),
        command=partial(handle_copy_response, tester_state, ui_refs),
    )
    copy_btn.pack(side="left", padx=(0, 8))
    clear_btn = ctk.CTkButton(
        actions_row, text="Clear Response", width=114, height=BTN_HEIGHT_SM, corner_radius=RADIUS_CONTROL,
        fg_color=BG_SURFACE, hover_color=COLOR_ERROR, border_width=1, border_color=BORDER_COLOR,
        text_color=TEXT_MUTED, font=font_ui(11, "bold"),
        command=partial(handle_clear_response, tester_state, ui_refs),
    )
    clear_btn.pack(side="left")

    error_label = ctk.CTkLabel(resp_card, text="", text_color=COLOR_ERROR, wraplength=max(240, avail_w - 28), justify="left", anchor="w", font=font_ui(12))
    error_label.pack(padx=14, pady=(0, 4), fill="x")

    response_box = ctk.CTkTextbox(
        resp_card, height=260, wrap="word", fg_color=BG_CODE, text_color=TEXT_MAIN,
        border_width=1, border_color=BORDER_COLOR, corner_radius=RADIUS_CONTROL, font=font_mono(11),
    )
    response_box.pack(padx=12, pady=(0, 12), fill="x")
    response_box.insert("1.0", DEFAULT_RESPONSE_PLACEHOLDER)
    response_box.configure(state="disabled")

    ui_refs["status_badge"] = status_badge
    ui_refs["time_label"] = time_label
    ui_refs["format_label"] = format_label
    ui_refs["error_label"] = error_label
    ui_refs["response_box"] = response_box
    ui_refs["copy_btn"] = copy_btn
    ui_refs["clear_btn"] = clear_btn
    return resp_card
