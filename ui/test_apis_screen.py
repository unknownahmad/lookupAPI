# ==========================================
# FINAL CODE
# ==========================================

from functools import partial
import customtkinter as ctk

from functions.request_history import HISTORY_FILE, load_request_history
from functions.test_catalogue import (
    extract_attribution_info,
    extract_rate_limit_info,
    format_example_endpoint,
    group_apis_by_category,
    load_verified_free_apis,
)
from ui.api_tester_panel import render_tester_panel
from ui.menu import add_text_card, wrap_long_text
from ui.request_history_panel import render_request_history_panel
from ui.theme import (
    ACCENT_PRIMARY, ACCENT_SECONDARY, BG_CARD, BG_CODE, BG_MAIN, BG_SURFACE,
    BG_SURFACE_HOVER, BORDER_COLOR, BORDER_SUBTLE, BTN_HEIGHT, BTN_HEIGHT_SM,
    COLOR_ERROR, COLOR_SUCCESS, COLOR_SUCCESS_TEXT, METHOD_COLORS, PAD_PAGE_X,
    RADIUS_BADGE, RADIUS_CONTROL, RADIUS_PANEL, TEXT_MAIN, TEXT_MUTED,
    TEXT_SECONDARY, font_mono, font_ui,
)


def add_test_apis_nav_button(sidebar, nav_buttons, command):
    """Add the Test APIs navigation item to the application sidebar."""
    btn = ctk.CTkButton(
        sidebar, text="  Test APIs", command=command, height=36, anchor="w",
        corner_radius=RADIUS_CONTROL, fg_color="transparent", hover_color=BG_SURFACE,
        text_color=TEXT_MUTED, font=font_ui(13),
    )
    btn.pack(padx=12, pady=2, fill="x")
    nav_buttons["test_apis"] = btn
    return btn


def refresh_history_button_label(history_btn, history_file=HISTORY_FILE):
    """Update the Request History button label with the current saved count."""
    if history_btn is not None and history_btn.winfo_exists():
        count = len(load_request_history(file_path=history_file))
        history_btn.configure(text=f"Request History ({count})")


def open_request_history(widgets, history_file=HISTORY_FILE):
    """Render the Test Request History panel inside the right-hand details container."""
    prev_btn = widgets.get("selected_api_btn")
    if prev_btn is not None and prev_btn.winfo_exists():
        prev_btn.configure(fg_color=BG_SURFACE, border_width=0)
        widgets["selected_api_btn"] = None

    render_request_history_panel(widgets["details_frame"], widgets["status_label"], history_file=history_file)
    refresh_history_button_label(widgets.get("history_btn"), history_file=history_file)


def render_test_api_details(details_frame, api, status_label, on_history_updated=None, history_file=HISTORY_FILE, widgets=None, clicked_btn=None):
    """Display full catalogue metadata, interactive tester, and usage terms for the selected API."""
    if widgets is not None and clicked_btn is not None:
        prev_btn = widgets.get("selected_api_btn")
        if prev_btn is not None and prev_btn.winfo_exists():
            prev_btn.configure(fg_color=BG_SURFACE, border_width=0)
        if clicked_btn.winfo_exists():
            clicked_btn.configure(fg_color=BG_SURFACE_HOVER, border_width=1, border_color=ACCENT_PRIMARY)
            widgets["selected_api_btn"] = clicked_btn

    for child in details_frame.winfo_children():
        child.destroy()
    if hasattr(details_frame, "_parent_canvas"):
        details_frame._parent_canvas.yview_moveto(0)

    details_frame.update_idletasks()
    panel_w = details_frame.winfo_width()
    avail_w = max(320, (panel_w if panel_w > 200 else 540) - 68)

    name = str(api.get("api_name") or "Not available")
    provider = str(api.get("provider") or "Not available")
    category = str(api.get("category") or "Not available")
    description = str(api.get("description") or "Not available")
    base_url = str(api.get("base_url") or "Not available")
    doc_url = str(api.get("documentation_url") or "Not available")
    endpoint_full = format_example_endpoint(api)
    auth_val = str(api.get("authentication") or "NONE")
    free_evidence = str(api.get("free_access_evidence") or "Not available")
    attribution = extract_attribution_info(api)
    rate_limits = extract_rate_limit_info(api)

    # 1. API Overview and Description
    overview = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    overview.pack(padx=6, pady=(6, 4), fill="x")
    ctk.CTkLabel(overview, text="API OVERVIEW", text_color=ACCENT_SECONDARY, font=font_ui(10, "bold")).pack(padx=14, pady=(10, 2), anchor="w")
    ctk.CTkLabel(overview, text=wrap_long_text(name, max(24, avail_w // 10)), text_color=TEXT_MAIN, wraplength=avail_w, justify="left", anchor="w", font=font_ui(16, "bold")).pack(padx=14, pady=(0, 8), fill="x")

    badges = ctk.CTkFrame(overview, fg_color="transparent")
    badges.pack(padx=14, pady=(0, 10), fill="x")
    ctk.CTkLabel(badges, text=f"  AUTH: {auth_val}  ", fg_color=COLOR_SUCCESS, text_color=COLOR_SUCCESS_TEXT, corner_radius=RADIUS_BADGE, font=font_ui(10, "bold")).pack(side="left", padx=(0, 8))
    for pill in [f"Category: {category}", f"Provider: {provider}"]:
        ctk.CTkLabel(badges, text=f"  {pill}  ", fg_color=BG_SURFACE, text_color=TEXT_SECONDARY, corner_radius=RADIUS_BADGE, wraplength=max(160, avail_w - 130), justify="left", font=font_ui(11)).pack(side="left", padx=(0, 8))

    ctk.CTkFrame(overview, height=1, fg_color=BORDER_SUBTLE).pack(padx=14, pady=(0, 8), fill="x")
    ctk.CTkLabel(overview, text=description, text_color=TEXT_SECONDARY, wraplength=max(240, avail_w - 16), justify="left", anchor="w", font=font_ui(12)).pack(padx=14, pady=(0, 12), fill="x")

    # 2. Documentation
    add_text_card(details_frame, "DOCUMENTATION", doc_url, ACCENT_SECONDARY, avail_w, wrap_mode="char", max_height=54, mono=True)

    # 3. Request Configuration & 4. Response Output
    render_tester_panel(
        details_frame, api, status_label, avail_w,
        on_history_updated=on_history_updated,
        history_file=history_file,
    )

    # 5. Additional API Information (Base URL, Example Endpoint, Attribution & Rate Limits)
    extra_card = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    extra_card.pack(padx=6, pady=(4, 8), fill="x")
    ctk.CTkLabel(extra_card, text="ADDITIONAL API INFORMATION", text_color=ACCENT_SECONDARY, font=font_ui(10, "bold")).pack(padx=14, pady=(10, 6), anchor="w")
    ctk.CTkFrame(extra_card, height=1, fg_color=BORDER_SUBTLE).pack(padx=12, pady=(0, 8), fill="x")

    base_block = ctk.CTkFrame(extra_card, fg_color=BG_SURFACE, corner_radius=RADIUS_CONTROL)
    base_block.pack(padx=12, pady=3, fill="x")
    ctk.CTkLabel(base_block, text="Base URL", text_color=ACCENT_PRIMARY, font=font_ui(11, "bold")).pack(padx=10, pady=(6, 2), anchor="w")
    ctk.CTkLabel(base_block, text=wrap_long_text(base_url, max(28, int(max(220, avail_w - 36) / 7.2))), text_color=TEXT_MAIN, wraplength=max(220, avail_w - 36), justify="left", anchor="w", font=font_mono(11)).pack(padx=10, pady=(0, 7), fill="x")

    ep_block = ctk.CTkFrame(extra_card, fg_color=BG_SURFACE, corner_radius=RADIUS_CONTROL)
    ep_block.pack(padx=12, pady=3, fill="x")
    ctk.CTkLabel(ep_block, text="Example GET Endpoint", text_color=ACCENT_SECONDARY, font=font_ui(11, "bold")).pack(padx=10, pady=(6, 3), anchor="w")
    ep_row = ctk.CTkFrame(ep_block, fg_color=BG_CODE, corner_radius=RADIUS_BADGE)
    ep_row.pack(padx=10, pady=(0, 8), fill="x")
    ep_row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(ep_row, text="GET", width=46, height=20, corner_radius=RADIUS_BADGE, anchor="center", fg_color=METHOD_COLORS["GET"], text_color=TEXT_MAIN, font=font_ui(10, "bold")).grid(row=0, column=0, padx=(8, 8), pady=6, sticky="nw")
    path_w = max(180, avail_w - 98)
    ctk.CTkLabel(ep_row, text=wrap_long_text(endpoint_full, max(24, int(path_w / 7.2))), text_color=TEXT_MAIN, wraplength=path_w, justify="left", anchor="w", font=font_mono(11, "bold")).grid(row=0, column=1, padx=(0, 8), pady=6, sticky="ew")

    info_rows = [
        ("Authentication", f"{auth_val} — No API key, token, account, or registration required"),
        ("Free Access Evidence", free_evidence),
        ("Attribution & License", attribution),
        ("Rate Limits & Usage Notes", rate_limits),
        ("Last Verified", f"{api.get('date_tested', 'Not available')}  ·  HTTP {api.get('http_status', 'N/A')}  ·  {api.get('response_time_seconds', 'N/A')}s"),
    ]
    for label_text, val_text in info_rows:
        block = ctk.CTkFrame(extra_card, fg_color=BG_SURFACE, corner_radius=RADIUS_CONTROL)
        block.pack(padx=12, pady=3, fill="x")
        ctk.CTkLabel(block, text=label_text, text_color=ACCENT_SECONDARY, font=font_ui(11, "bold")).pack(padx=10, pady=(6, 1), anchor="w")
        ctk.CTkLabel(block, text=val_text, text_color=TEXT_SECONDARY, wraplength=max(240, avail_w - 36), justify="left", anchor="w", font=font_ui(12)).pack(padx=10, pady=(0, 7), fill="x")
    ctk.CTkFrame(extra_card, height=6, fg_color="transparent").pack(fill="x")

    status_label.configure(text=f"Selected: {name[:55]} ({category}) — Ready to send request.", text_color=ACCENT_SECONDARY)


def populate_category_list(category, state, widgets):
    """Render approved APIs in the left panel filtered by the selected category."""
    list_frame = widgets["list_frame"]
    count_label = widgets["count_label"]
    widgets["selected_api_btn"] = None

    for child in list_frame.winfo_children():
        child.destroy()

    for cat_key, btn in widgets["category_buttons"].items():
        if cat_key == category:
            btn.configure(fg_color=ACCENT_PRIMARY, text_color=TEXT_MAIN)
        else:
            btn.configure(fg_color=BG_SURFACE, text_color=TEXT_MUTED)

    grouped = state["grouped"]
    categories_to_show = list(grouped.keys()) if category == "All" else ([category] if category in grouped else [])
    total_shown = sum(len(grouped[c]) for c in categories_to_show)
    count_label.configure(text=f"{total_shown} verified free APIs · {category}")

    if total_shown == 0:
        ctk.CTkLabel(list_frame, text="No verified APIs found in this category.", text_color=TEXT_MUTED, font=font_ui(12)).pack(padx=10, pady=14, anchor="w")
        return

    on_history_updated = widgets.get("on_history_updated")
    history_file = state.get("history_file", HISTORY_FILE)

    for cat_name in categories_to_show:
        ctk.CTkLabel(list_frame, text=cat_name.upper(), text_color=TEXT_MUTED, font=font_ui(10, "bold")).pack(padx=8, pady=(10, 3), anchor="w")
        for api in grouped[cat_name]:
            raw_name = str(api.get("api_name") or "Not available")
            raw_prov = str(api.get("provider") or "Not available")
            short_name = raw_name if len(raw_name) <= 32 else raw_name[:29] + "..."
            short_prov = raw_prov if len(raw_prov) <= 30 else raw_prov[:27] + "..."
            btn = ctk.CTkButton(
                list_frame, text=f"{short_name}\n{short_prov}",
                height=44, corner_radius=RADIUS_CONTROL, anchor="w",
                fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER,
                text_color=TEXT_MAIN, font=font_ui(12),
            )
            btn.configure(
                command=partial(
                    render_test_api_details,
                    widgets["details_frame"], api, widgets["status_label"],
                    on_history_updated, history_file, widgets, btn,
                )
            )
            btn.pack(padx=4, pady=3, fill="x")


def show_test_apis_screen(content_frame, on_back, history_file=HISTORY_FILE):
    """Build and display the Test APIs verified free catalogue, API tester, and request history screen."""
    apis = load_verified_free_apis()
    grouped = group_apis_by_category(apis)
    state = {"apis": apis, "grouped": grouped, "history_file": history_file}

    header = ctk.CTkFrame(content_frame, fg_color="transparent")
    header.pack(padx=PAD_PAGE_X, pady=(18, 8), fill="x")

    title_col = ctk.CTkFrame(header, fg_color="transparent")
    title_col.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(title_col, text="Test APIs", font=font_ui(20, "bold"), text_color=TEXT_MAIN).pack(anchor="w")
    ctk.CTkLabel(title_col, text="Verified unauthenticated public APIs · Send GET, POST, PUT, and DELETE requests", font=font_ui(12), text_color=TEXT_MUTED).pack(anchor="w")

    ctk.CTkButton(
        header, text="← Back to Home", command=on_back, width=118, height=BTN_HEIGHT,
        corner_radius=RADIUS_CONTROL, fg_color=BG_CARD, hover_color=BG_SURFACE,
        border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MUTED, font=font_ui(12),
    ).pack(side="right", anchor="n")

    history_count = len(load_request_history(file_path=history_file))
    history_btn = ctk.CTkButton(
        header, text=f"Request History ({history_count})", width=150, height=BTN_HEIGHT,
        corner_radius=RADIUS_CONTROL, fg_color=BG_SURFACE, hover_color=ACCENT_PRIMARY,
        border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MAIN, font=font_ui(12, "bold"),
    )
    history_btn.pack(side="right", padx=(0, 8), anchor="n")

    cat_bar = ctk.CTkFrame(content_frame, fg_color=BG_CARD, corner_radius=RADIUS_PANEL, border_width=1, border_color=BORDER_COLOR)
    cat_bar.pack(padx=PAD_PAGE_X, pady=(0, 10), fill="x")

    body = ctk.CTkFrame(content_frame, fg_color="transparent")
    body.pack(padx=PAD_PAGE_X, pady=(0, 18), fill="both", expand=True)
    body.grid_columnconfigure(0, weight=1, uniform="split")
    body.grid_columnconfigure(1, weight=2, uniform="split")
    body.grid_rowconfigure(0, weight=1)

    left_panel = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=RADIUS_PANEL, border_width=1, border_color=BORDER_COLOR)
    left_panel.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
    count_label = ctk.CTkLabel(left_panel, text="", font=font_ui(11, "bold"), text_color=TEXT_MUTED)
    count_label.pack(padx=12, pady=(10, 4), anchor="w")
    list_frame = ctk.CTkScrollableFrame(left_panel, fg_color=BG_MAIN, corner_radius=RADIUS_CONTROL)
    list_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)

    right_panel = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=RADIUS_PANEL, border_width=1, border_color=BORDER_COLOR)
    right_panel.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
    details_frame = ctk.CTkScrollableFrame(right_panel, fg_color=BG_MAIN, corner_radius=RADIUS_CONTROL, border_width=1, border_color=BORDER_COLOR)
    details_frame.pack(padx=14, pady=(14, 8), fill="both", expand=True)

    status_label = ctk.CTkLabel(right_panel, text="", font=font_ui(12), text_color=TEXT_MUTED)
    status_label.pack(padx=14, pady=(0, 12), anchor="w")

    on_history_updated = partial(refresh_history_button_label, history_btn, history_file)
    widgets = {
        "list_frame": list_frame, "count_label": count_label,
        "details_frame": details_frame, "status_label": status_label,
        "category_buttons": {}, "history_btn": history_btn,
        "on_history_updated": on_history_updated, "selected_api_btn": None,
    }
    history_btn.configure(command=partial(open_request_history, widgets, history_file))

    if len(apis) == 0:
        ctk.CTkLabel(details_frame, text="Could not load data/verified_free_apis.json.", text_color=COLOR_ERROR, font=font_ui(13)).pack(padx=14, pady=18, anchor="w")
        status_label.configure(text="Verified API catalogue is unavailable.", text_color=COLOR_ERROR)
        return

    ctk.CTkLabel(
        details_frame,
        text="Select any verified no-auth API from the catalogue on the left to inspect its details and send HTTP requests, or open Request History above to review previous runs.",
        text_color=TEXT_MUTED, wraplength=440, justify="left", font=font_ui(12),
    ).pack(padx=14, pady=18, anchor="w")
    status_label.configure(text=f"Loaded {len(apis)} verified free APIs across {len(grouped)} categories.", text_color=TEXT_MUTED)

    cat_grid = ctk.CTkFrame(cat_bar, fg_color="transparent")
    cat_grid.pack(padx=8, pady=6, fill="x")
    cat_grid.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="cats")
    all_categories = ["All"] + list(grouped.keys())
    for idx, cat in enumerate(all_categories):
        cnt = len(apis) if cat == "All" else len(grouped[cat])
        btn = ctk.CTkButton(
            cat_grid, text=f"{cat} ({cnt})", height=BTN_HEIGHT_SM, corner_radius=RADIUS_CONTROL,
            fg_color=BG_SURFACE, hover_color=BG_SURFACE_HOVER, text_color=TEXT_MUTED,
            font=font_ui(11, "bold"), command=partial(populate_category_list, cat, state, widgets),
        )
        btn.grid(row=idx // 5, column=idx % 5, padx=3, pady=3, sticky="ew")
        widgets["category_buttons"][cat] = btn

    populate_category_list("All", state, widgets)
