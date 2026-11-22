# ==========================================
# FINAL CODE
# ==========================================

from functools import partial
import queue
import threading
import customtkinter as ctk

from functions.api_tester import SUPPORTED_METHODS, build_default_request, send_api_request
from functions.request_history import HISTORY_FILE, save_request_history
from ui.response_panel import build_response_card, update_response_card
from ui.theme import (
    ACCENT_HOVER, ACCENT_PRIMARY, ACCENT_SECONDARY, BG_CARD, BG_CODE,
    BG_SURFACE, BG_SURFACE_HOVER, BORDER_COLOR, BORDER_SUBTLE, BTN_HEIGHT,
    BTN_HEIGHT_SM, COLOR_ERROR, COLOR_INFO_TEXT, METHOD_COLORS, RADIUS_CONTROL,
    TEXT_MAIN, TEXT_MUTED, TEXT_SECONDARY, font_mono, font_ui,
)


def remove_key_value_row(row_entry, rows_list):
    """Remove a single editable key-value row from its container and tracking list."""
    if row_entry in rows_list:
        rows_list.remove(row_entry)
    row_entry["frame"].destroy()


def add_key_value_row(container, rows_list, key_text="", value_text="", key_placeholder="Key", value_placeholder="Value"):
    """Append an editable key-value input row with a remove button."""
    row_frame = ctk.CTkFrame(container, fg_color="transparent")
    row_frame.pack(pady=2, fill="x")
    row_frame.grid_columnconfigure(0, weight=2)
    row_frame.grid_columnconfigure(1, weight=3)

    key_entry = ctk.CTkEntry(
        row_frame, height=30, corner_radius=RADIUS_CONTROL, fg_color=BG_SURFACE,
        border_color=BORDER_COLOR, text_color=TEXT_MAIN, placeholder_text=key_placeholder,
        font=font_mono(11),
    )
    if key_text:
        key_entry.insert(0, str(key_text))
    key_entry.grid(row=0, column=0, padx=(0, 6), sticky="ew")

    val_entry = ctk.CTkEntry(
        row_frame, height=30, corner_radius=RADIUS_CONTROL, fg_color=BG_SURFACE,
        border_color=BORDER_COLOR, text_color=TEXT_MAIN, placeholder_text=value_placeholder,
        font=font_mono(11),
    )
    if value_text:
        val_entry.insert(0, str(value_text))
    val_entry.grid(row=0, column=1, padx=(0, 6), sticky="ew")

    row_entry = {"frame": row_frame, "key": key_entry, "value": val_entry}
    rows_list.append(row_entry)

    ctk.CTkButton(
        row_frame, text="✕", width=30, height=30, corner_radius=RADIUS_CONTROL,
        fg_color=BG_SURFACE, hover_color=COLOR_ERROR, text_color=TEXT_MUTED,
        font=font_ui(11, "bold"),
        command=partial(remove_key_value_row, row_entry, rows_list),
    ).grid(row=0, column=2)


def collect_key_value_pairs(rows_list):
    """Read all non-empty key-value inputs from the UI into a dictionary."""
    result = {}
    for row in rows_list:
        if not row["frame"].winfo_exists():
            continue
        key = row["key"].get().strip()
        val = row["value"].get().strip()
        if key:
            result[key] = val
    return result


def on_method_change(selected_method, tester_state, ui_refs):
    """Update HTTP method styling and toggle the JSON request body editor."""
    method = str(selected_method or "GET").strip().upper()
    tester_state["method"] = method
    color = METHOD_COLORS.get(method, ACCENT_PRIMARY)
    ui_refs["method_menu"].configure(fg_color=color, button_color=color)

    if method in ("POST", "PUT"):
        ui_refs["delete_note"].pack_forget()
        ui_refs["body_section"].pack(padx=12, pady=(0, 12), fill="x")
        ui_refs["status_label"].configure(
            text=f"Method set to {method} — enter an optional JSON body and click Send Request.",
            text_color=ACCENT_SECONDARY,
        )
    elif method == "DELETE":
        ui_refs["body_section"].pack_forget()
        ui_refs["delete_note"].pack(padx=12, pady=(0, 12), fill="x")
        ui_refs["status_label"].configure(
            text="Method set to DELETE — sends without a body by default.",
            text_color=TEXT_MUTED,
        )
    else:
        ui_refs["body_section"].pack_forget()
        ui_refs["delete_note"].pack_forget()
        ui_refs["status_label"].configure(text="Method set to GET — ready to send request.", text_color=TEXT_MUTED)


def request_worker(method, url, params, headers, json_body, result_queue):
    """Run send_api_request in a background thread and return its result via a queue."""
    outcome = send_api_request(method, url, params=params, headers=headers, json_body=json_body)
    result_queue.put(outcome)


def apply_test_response(result, ui_refs, tester_state=None):
    """Display the completed HTTP status, timing, error message, and formatted body."""
    update_response_card(result, tester_state if tester_state is not None else {}, ui_refs)


def poll_test_response(result_queue, req_id, request_url, tester_state, ui_refs):
    """Poll the worker queue on the main Tkinter thread without freezing the GUI."""
    if not ui_refs["response_box"].winfo_exists():
        return
    if req_id != tester_state["request_id"]:
        return

    try:
        result = result_queue.get_nowait()
    except queue.Empty:
        ui_refs["response_box"].after(
            40,
            partial(poll_test_response, result_queue, req_id, request_url, tester_state, ui_refs),
        )
        return

    tester_state["in_flight"] = False
    tester_state["last_result"] = result

    if tester_state.get("record_history", True):
        save_request_history(
            tester_state.get("api_name", "Custom Request"),
            result.get("method") or tester_state.get("method", "GET"),
            request_url,
            result,
            file_path=tester_state.get("history_file", HISTORY_FILE),
        )
        on_updated = tester_state.get("on_history_updated")
        if callable(on_updated):
            on_updated()

    apply_test_response(result, ui_refs, tester_state)


def handle_send_request(tester_state, ui_refs):
    """Collect request inputs and execute the selected HTTP request on a background thread."""
    if tester_state["in_flight"]:
        return

    method = ui_refs["method_menu"].get().strip().upper()
    tester_state["method"] = method
    url = ui_refs["url_entry"].get().strip()
    params = collect_key_value_pairs(tester_state["param_rows"])
    headers = collect_key_value_pairs(tester_state["header_rows"])
    raw_body = ui_refs["body_box"].get("1.0", "end").strip() if method in ("POST", "PUT") else None

    tester_state["request_id"] += 1
    req_id = tester_state["request_id"]
    tester_state["in_flight"] = True

    ui_refs["send_btn"].configure(state="disabled", text="Sending...")
    ui_refs["status_badge"].configure(text="  Sending...  ", fg_color=ACCENT_SECONDARY, text_color=COLOR_INFO_TEXT)
    ui_refs["time_label"].configure(text="Time: ...")
    ui_refs["format_label"].configure(text="", fg_color="transparent", text_color=TEXT_MUTED)
    ui_refs["error_label"].configure(text="", text_color=TEXT_MUTED)
    ui_refs["status_label"].configure(text=f"Sending {method} request...", text_color=ACCENT_SECONDARY)

    resp_box = ui_refs["response_box"]
    resp_box.configure(state="normal")
    resp_box.delete("1.0", "end")
    resp_box.insert("1.0", f"Sending {method} request, waiting for response...")
    resp_box.configure(state="disabled")

    result_queue = queue.Queue()
    worker = threading.Thread(
        target=request_worker,
        args=(method, url, params, headers, raw_body, result_queue),
        daemon=True,
    )
    worker.start()
    resp_box.after(40, partial(poll_test_response, result_queue, req_id, url, tester_state, ui_refs))


def render_tester_panel(details_frame, api, status_label, avail_w, on_history_updated=None, history_file=HISTORY_FILE):
    """Build the interactive Request Configuration and Response cards for the selected API."""
    defaults = build_default_request(api)
    api_name = str(api.get("api_name") or "Custom Request").strip() or "Custom Request"
    tester_state = {
        "api_name": api_name,
        "method": defaults["method"],
        "param_rows": [],
        "header_rows": [],
        "request_id": 0,
        "in_flight": False,
        "last_result": None,
        "last_body": "",
        "record_history": True,
        "history_file": history_file,
        "on_history_updated": on_history_updated,
    }
    ui_refs = {"status_label": status_label}

    req_card = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    req_card.pack(padx=6, pady=(6, 6), fill="x")

    req_hdr = ctk.CTkFrame(req_card, fg_color="transparent")
    req_hdr.pack(padx=14, pady=(10, 6), fill="x")
    ctk.CTkLabel(req_hdr, text="REQUEST CONFIGURATION", text_color=ACCENT_SECONDARY, font=font_ui(10, "bold")).pack(side="left")
    ctk.CTkLabel(req_hdr, text="Edit URL, params, headers, or body before sending", text_color=TEXT_MUTED, font=font_ui(10)).pack(side="right")
    ctk.CTkFrame(req_card, height=1, fg_color=BORDER_SUBTLE).pack(padx=12, pady=(0, 10), fill="x")

    url_row = ctk.CTkFrame(req_card, fg_color="transparent")
    url_row.pack(padx=12, pady=(0, 10), fill="x")
    url_row.grid_columnconfigure(1, weight=1)

    method_menu = ctk.CTkOptionMenu(
        url_row, values=list(SUPPORTED_METHODS), width=92, height=BTN_HEIGHT, corner_radius=RADIUS_CONTROL,
        fg_color=METHOD_COLORS["GET"], button_color=METHOD_COLORS["GET"],
        button_hover_color=ACCENT_HOVER, dropdown_fg_color=BG_SURFACE,
        dropdown_hover_color=ACCENT_PRIMARY, text_color=TEXT_MAIN,
        font=font_ui(11, "bold"),
        command=partial(on_method_change, tester_state=tester_state, ui_refs=ui_refs),
    )
    method_menu.set("GET")
    method_menu.grid(row=0, column=0, padx=(0, 8))

    url_entry = ctk.CTkEntry(
        url_row, height=BTN_HEIGHT, corner_radius=RADIUS_CONTROL, fg_color=BG_SURFACE,
        border_color=BORDER_COLOR, text_color=TEXT_MAIN, placeholder_text="https://...",
        font=font_mono(11),
    )
    url_entry.insert(0, defaults["url"])
    url_entry.grid(row=0, column=1, padx=(0, 8), sticky="ew")

    send_btn = ctk.CTkButton(
        url_row, text="Send Request", width=114, height=BTN_HEIGHT, corner_radius=RADIUS_CONTROL,
        fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, text_color=TEXT_MAIN,
        font=font_ui(12, "bold"), command=partial(handle_send_request, tester_state, ui_refs),
    )
    send_btn.grid(row=0, column=2)

    params_header = ctk.CTkFrame(req_card, fg_color="transparent")
    params_header.pack(padx=12, pady=(2, 4), fill="x")
    ctk.CTkLabel(params_header, text="Query Parameters", text_color=TEXT_SECONDARY, font=font_ui(12, "bold")).pack(side="left")
    params_box = ctk.CTkFrame(req_card, fg_color="transparent")
    params_box.pack(padx=12, pady=(0, 8), fill="x")
    ctk.CTkButton(
        params_header, text="+ Add Parameter", width=116, height=BTN_HEIGHT_SM, corner_radius=RADIUS_CONTROL,
        fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER, border_width=1, border_color=BORDER_COLOR,
        text_color=TEXT_MAIN, font=font_ui(11),
        command=partial(add_key_value_row, params_box, tester_state["param_rows"], "", "", "Parameter name", "Parameter value"),
    ).pack(side="right")
    for p_key, p_val in defaults["params"].items():
        add_key_value_row(params_box, tester_state["param_rows"], p_key, p_val, "Parameter name", "Parameter value")

    headers_header = ctk.CTkFrame(req_card, fg_color="transparent")
    headers_header.pack(padx=12, pady=(2, 4), fill="x")
    ctk.CTkLabel(headers_header, text="Request Headers", text_color=TEXT_SECONDARY, font=font_ui(12, "bold")).pack(side="left")
    headers_box = ctk.CTkFrame(req_card, fg_color="transparent")
    headers_box.pack(padx=12, pady=(0, 12), fill="x")
    ctk.CTkButton(
        headers_header, text="+ Add Header", width=104, height=BTN_HEIGHT_SM, corner_radius=RADIUS_CONTROL,
        fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER, border_width=1, border_color=BORDER_COLOR,
        text_color=TEXT_MAIN, font=font_ui(11),
        command=partial(add_key_value_row, headers_box, tester_state["header_rows"], "", "", "Header name", "Header value"),
    ).pack(side="right")
    for h_key, h_val in defaults["headers"].items():
        add_key_value_row(headers_box, tester_state["header_rows"], h_key, h_val, "Header name", "Header value")

    body_section = ctk.CTkFrame(req_card, fg_color="transparent")
    body_header = ctk.CTkFrame(body_section, fg_color="transparent")
    body_header.pack(pady=(2, 4), fill="x")
    ctk.CTkLabel(body_header, text="JSON Request Body", text_color=TEXT_SECONDARY, font=font_ui(12, "bold")).pack(side="left")
    ctk.CTkLabel(body_header, text="Optional JSON object or array (validated before sending)", text_color=TEXT_MUTED, font=font_ui(10)).pack(side="right")
    body_box = ctk.CTkTextbox(
        body_section, height=115, wrap="word", fg_color=BG_CODE, text_color=TEXT_MAIN,
        border_width=1, border_color=BORDER_COLOR, corner_radius=RADIUS_CONTROL, font=font_mono(11),
    )
    body_box.pack(fill="x")

    delete_note = ctk.CTkLabel(
        req_card, text="DELETE requests are sent without a request body by default. Only run against safe test endpoints.",
        text_color=TEXT_MUTED, wraplength=max(240, avail_w - 28), justify="left", anchor="w", font=font_ui(11),
    )

    ui_refs.update({
        "method_menu": method_menu,
        "url_entry": url_entry,
        "send_btn": send_btn,
        "body_section": body_section,
        "body_box": body_box,
        "delete_note": delete_note,
    })
    build_response_card(details_frame, tester_state, ui_refs, avail_w)

    details_frame.tester_state = tester_state
    details_frame.tester_ui = ui_refs
    return tester_state, ui_refs
