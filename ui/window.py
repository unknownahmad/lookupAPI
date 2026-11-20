from functools import partial
import customtkinter as ctk

from functions.api_details import get_api_details
from functions.api_directory import get_api_directory, search_apis
from functions.saved_apis import get_saved_APIs, save_API
from ui.menu import (
    ACCENT_HOVER, ACCENT_PRIMARY, ACCENT_SECONDARY, BG_CARD, BG_MAIN,
    BG_SURFACE, BORDER_COLOR, COLOR_ERROR, COLOR_SUCCESS, COLOR_WARNING,
    FONT_FAMILY, METHOD_COLORS, TEXT_MAIN, TEXT_MUTED, add_text_card,
    create_sidebar, show_activity_screen, show_home_screen,
    show_saved_apis_screen, wrap_long_text,
)

MAX_VISIBLE_RESULTS = 75
MAX_VISIBLE_ENDPOINTS = 50


def clear_frame(frame):
    """Remove all child widgets from a container frame."""
    for child in frame.winfo_children():
        child.destroy()


def render_discover_details(details_frame, api, details):
    """Render structured, wrapped overview, links, and endpoints for a discovered API."""
    clear_frame(details_frame)
    if hasattr(details_frame, "_parent_canvas"):
        details_frame._parent_canvas.yview_moveto(0)

    details_frame.update_idletasks()
    panel_w = details_frame.winfo_width()
    avail_w = max(320, (panel_w if panel_w > 200 else 540) - 68)

    data = details if details is not None else api
    name = str(data.get("name") or api.get("name") or "Not available").strip() or "Not available"
    provider = str(api.get("provider") or data.get("provider") or "Not available").strip() or "Not available"
    version = str(data.get("version") or api.get("version") or "Not available").strip() or "Not available"
    doc_url = str(data.get("documentation_url") or api.get("documentation_url") or "").strip() or "Not available"
    base_url = str(data.get("base_url") or "").strip() or "Not available"
    description = str(data.get("description") or api.get("description") or "").strip() or "Not available"

    overview = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
    overview.pack(padx=6, pady=(6, 4), fill="x")
    ctk.CTkLabel(overview, text="API OVERVIEW", text_color=ACCENT_SECONDARY, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")).pack(padx=14, pady=(10, 2), anchor="w")
    ctk.CTkLabel(overview, text=wrap_long_text(name, max(24, avail_w // 10)), text_color=TEXT_MAIN, wraplength=avail_w, justify="left", anchor="w", font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")).pack(padx=14, pady=(0, 8), fill="x")

    meta_row = ctk.CTkFrame(overview, fg_color="transparent")
    meta_row.pack(padx=14, pady=(0, 12), fill="x")
    stack_meta = len(provider) + len(version) > 42
    for badge_text in [f"Provider: {provider}", f"Version: {version}"]:
        lbl = ctk.CTkLabel(meta_row, text=f"  {wrap_long_text(badge_text, max(28, avail_w // 8))}  ", fg_color=BG_SURFACE, text_color=TEXT_MAIN, corner_radius=4, wraplength=avail_w - 12, justify="left", anchor="w", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"))
        lbl.pack(pady=(0, 4), anchor="w") if stack_meta else lbl.pack(side="left", padx=(0, 8))

    add_text_card(details_frame, "DESCRIPTION", description, TEXT_MUTED, avail_w, wrap_mode="word", max_height=180)
    add_text_card(details_frame, "DOCUMENTATION", doc_url, ACCENT_SECONDARY, avail_w, wrap_mode="char", max_height=76)
    add_text_card(details_frame, "BASE URL", base_url, ACCENT_PRIMARY, avail_w, wrap_mode="char", max_height=76)

    ep_card = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
    ep_card.pack(padx=6, pady=(4, 8), fill="x")
    endpoints = (details.get("endpoints") or []) if details is not None else []
    ctk.CTkLabel(ep_card, text=f"AVAILABLE ENDPOINTS ({len(endpoints)})", text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")).pack(padx=14, pady=(10, 6), anchor="w")

    if len(endpoints) == 0:
        msg = "Not available" if details is None else "No endpoints listed in this specification."
        ctk.CTkLabel(ep_card, text=msg, text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=14, pady=(0, 10), anchor="w")
        return

    path_wrap_w = max(180, avail_w - 96)
    path_chars = max(24, int(path_wrap_w / 7.5))
    desc_wrap_w = max(240, avail_w - 36)
    desc_chars = max(32, int(desc_wrap_w / 7.0))

    for ep in endpoints[:MAX_VISIBLE_ENDPOINTS]:
        method = str(ep.get("method") or "GET").upper()
        path = str(ep.get("path") or "/")
        summary = str(ep.get("summary") or "Not available").strip() or "Not available"

        row = ctk.CTkFrame(ep_card, fg_color=BG_SURFACE, corner_radius=5)
        row.pack(padx=12, pady=3, fill="x")
        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(padx=8, pady=(6, 2), fill="x")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text=method, width=54, height=22, corner_radius=4, anchor="center", fg_color=METHOD_COLORS.get(method, ACCENT_PRIMARY), text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")).grid(row=0, column=0, padx=(0, 8), sticky="nw")
        ctk.CTkLabel(top, text=wrap_long_text(path, path_chars), text_color=TEXT_MAIN, wraplength=path_wrap_w, justify="left", anchor="w", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")).grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(row, text=wrap_long_text(summary, desc_chars), text_color=TEXT_MUTED, wraplength=desc_wrap_w, justify="left", anchor="w", font=ctk.CTkFont(family=FONT_FAMILY, size=11)).pack(padx=10, pady=(2, 7), fill="x")

    if len(endpoints) > MAX_VISIBLE_ENDPOINTS:
        note = f"Showing first {MAX_VISIBLE_ENDPOINTS} of {len(endpoints)} endpoints."
        ctk.CTkLabel(ep_card, text=note, text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=11)).pack(padx=14, pady=(4, 10), anchor="w")


def select_discover_api(api, state, widgets):
    """Fetch full specification details for the chosen API and update the panel."""
    details_frame = widgets["details_frame"]
    status_label = widgets["status_label"]

    status_label.configure(text=f"Loading specification for '{str(api.get('name') or '')[:45]}'...", text_color=ACCENT_SECONDARY)
    clear_frame(details_frame)
    ctk.CTkLabel(details_frame, text="Loading OpenAPI specification and endpoints, please wait...", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=14, pady=18, anchor="w")
    status_label.update_idletasks()

    details = get_api_details(api)
    if details is not None:
        selected = dict(api)
        selected.update(details)
        state["selected_api"] = selected
        status_label.configure(text=f"Loaded '{str(selected.get('name') or '')[:45]}' ({len(details.get('endpoints', []))} endpoints).", text_color=COLOR_SUCCESS)
    else:
        state["selected_api"] = dict(api)
        status_label.configure(text="Loaded basic info (full specification unavailable).", text_color=COLOR_WARNING)

    render_discover_details(details_frame, api, details)


def render_discover_list(apis, state, widgets):
    """Populate the scrollable catalog list with matching API buttons."""
    list_frame = widgets["list_frame"]
    count_label = widgets["count_label"]

    clear_frame(list_frame)
    total = len(apis)
    visible = apis[:MAX_VISIBLE_RESULTS]

    if total == 0:
        count_label.configure(text="0 APIs found")
        ctk.CTkLabel(list_frame, text="No matching APIs found.", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=10, pady=14, anchor="w")
        return

    if total > MAX_VISIBLE_RESULTS:
        count_label.configure(text=f"{total} APIs available (showing top {MAX_VISIBLE_RESULTS} — type to filter)")
    else:
        count_label.configure(text=f"Showing {total} matching APIs")

    for api in visible:
        raw_name = str(api.get("name") or "Not available")
        raw_prov = str(api.get("provider") or "Not available")
        name_txt = raw_name if len(raw_name) <= 34 else raw_name[:31] + "..."
        prov_txt = raw_prov if len(raw_prov) <= 30 else raw_prov[:27] + "..."
        ctk.CTkButton(
            list_frame, text=f"{name_txt}\nProvider: {prov_txt}",
            command=partial(select_discover_api, api, state, widgets),
            height=42, corner_radius=6, anchor="w", fg_color=BG_SURFACE,
            hover_color=ACCENT_PRIMARY, text_color=TEXT_MAIN,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        ).pack(padx=4, pady=3, fill="x")


def handle_discover_search(state, widgets, _event=None):
    """Filter the loaded API catalog using the current search input."""
    query = widgets["search_entry"].get()
    results = search_apis(query, state["directory"])
    render_discover_list(results, state, widgets)


def handle_save_api(state, widgets):
    """Save the selected API and display success, duplicate, or error feedback."""
    selected = state.get("selected_api")
    status_label = widgets["status_label"]

    if not selected:
        status_label.configure(text="Please select an API from the list before saving.", text_color=COLOR_WARNING)
        return

    api_name = str(selected.get("name") or "").strip()[:100]
    existing_names = {str(item.get("name") or "").strip().lower() for item in get_saved_APIs()}

    if save_API(selected):
        status_label.configure(text="API saved successfully", text_color=COLOR_SUCCESS)
    elif api_name.lower() in existing_names:
        status_label.configure(text="This API is already saved", text_color=COLOR_WARNING)
    else:
        status_label.configure(text="Could not save API. Please try again.", text_color=COLOR_ERROR)


def show_discover_screen(content_frame, state, on_back):
    """Build and display the Discover APIs catalog and details screen."""
    state["selected_api"] = None

    header = ctk.CTkFrame(content_frame, fg_color="transparent")
    header.pack(padx=24, pady=(18, 8), fill="x")
    ctk.CTkLabel(header, text="Discover APIs", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
    ctk.CTkButton(header, text="← Back to Home", command=on_back, width=120, height=30, corner_radius=6, fg_color=BG_CARD, hover_color=BG_SURFACE, border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="right")

    search_row = ctk.CTkFrame(content_frame, fg_color="transparent")
    search_row.pack(padx=24, pady=(0, 10), fill="x")
    search_entry = ctk.CTkEntry(search_row, height=34, corner_radius=6, fg_color=BG_CARD, border_color=BORDER_COLOR, text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=13), placeholder_text="Filter catalog by API name or provider (e.g. GitHub, Google, Stripe)...")
    search_entry.pack(side="left", padx=(0, 8), fill="x", expand=True)

    body = ctk.CTkFrame(content_frame, fg_color="transparent")
    body.pack(padx=24, pady=(0, 20), fill="both", expand=True)
    body.grid_columnconfigure(0, weight=1, uniform="split")
    body.grid_columnconfigure(1, weight=2, uniform="split")
    body.grid_rowconfigure(0, weight=1)

    left_panel = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
    left_panel.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
    count_label = ctk.CTkLabel(left_panel, text="Loading API directory...", font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"), text_color=TEXT_MUTED)
    count_label.pack(padx=12, pady=(10, 4), anchor="w")
    list_frame = ctk.CTkScrollableFrame(left_panel, fg_color=BG_MAIN, corner_radius=6)
    list_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)

    right_panel = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
    right_panel.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
    details_frame = ctk.CTkScrollableFrame(right_panel, fg_color=BG_MAIN, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
    details_frame.pack(padx=14, pady=(14, 8), fill="both", expand=True)
    ctk.CTkLabel(details_frame, text="Select an API from the catalog on the left to inspect its overview, documentation, base URL, and endpoints.", text_color=TEXT_MUTED, wraplength=420, justify="left", font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=14, pady=18, anchor="w")

    status_label = ctk.CTkLabel(right_panel, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED)
    status_label.pack(padx=14, pady=(0, 6), anchor="w")

    widgets = {"search_entry": search_entry, "count_label": count_label, "list_frame": list_frame, "details_frame": details_frame, "status_label": status_label}
    ctk.CTkButton(search_row, text="Search", command=partial(handle_discover_search, state, widgets), width=88, height=34, corner_radius=6, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")).pack(side="left")
    search_entry.bind("<KeyRelease>", partial(handle_discover_search, state, widgets))
    ctk.CTkButton(right_panel, text="Save API", command=partial(handle_save_api, state, widgets), height=32, corner_radius=6, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")).pack(padx=14, pady=(0, 14), anchor="w")

    if len(state["directory"]) == 0:
        status_label.configure(text="Loading API directory from APIs.guru...", text_color=ACCENT_SECONDARY)
        content_frame.update_idletasks()
        state["directory"] = get_api_directory()

    if len(state["directory"]) == 0:
        status_label.configure(text="Could not load APIs.guru directory. Check your connection.", text_color=COLOR_ERROR)
    else:
        status_label.configure(text="Catalog ready. Select an API to view specification details.", text_color=TEXT_MUTED)
    render_discover_list(state["directory"], state, widgets)


def navigate_to(section, content_frame, state, callbacks):
    """Switch the main content area to the selected section and update sidebar state."""
    clear_frame(content_frame)
    for nav_key, btn in state.get("nav_buttons", {}).items():
        if nav_key == section:
            btn.configure(fg_color=BG_SURFACE, text_color=TEXT_MAIN, border_width=1, border_color=ACCENT_PRIMARY)
        else:
            btn.configure(fg_color="transparent", text_color=TEXT_MUTED, border_width=0)

    if section == "home":
        show_home_screen(content_frame, callbacks)
    elif section == "discover":
        show_discover_screen(content_frame, state, callbacks["home"])
    elif section == "saved":
        show_saved_apis_screen(content_frame, callbacks["home"])
    elif section == "activity":
        show_activity_screen(content_frame, callbacks["home"])


def start_application(auto_mainloop=True):
    """Initialize the main LOOKUPAPI window and start the GUI event loop."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    window = ctk.CTk()
    window.title("LOOKUPAPI — API Discovery Platform")
    window.geometry("1160x720")
    window.minsize(980, 620)
    window.configure(fg_color=BG_MAIN)

    state = {"directory": [], "selected_api": None, "nav_buttons": {}}
    content_frame = ctk.CTkFrame(window, corner_radius=0, fg_color=BG_MAIN)

    callbacks = {}
    callbacks["home"] = partial(navigate_to, "home", content_frame, state, callbacks)
    callbacks["discover"] = partial(navigate_to, "discover", content_frame, state, callbacks)
    callbacks["saved"] = partial(navigate_to, "saved", content_frame, state, callbacks)
    callbacks["activity"] = partial(navigate_to, "activity", content_frame, state, callbacks)
    callbacks["exit"] = window.destroy

    state["nav_buttons"] = create_sidebar(window, callbacks)
    content_frame.pack(side="right", fill="both", expand=True)
    window.lookup_state = state
    window.lookup_callbacks = callbacks
    window.lookup_content = content_frame

    navigate_to("home", content_frame, state, callbacks)
    if auto_mainloop:
        window.mainloop()
    return window
