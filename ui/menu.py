# ==========================================
# MIDTERM CODE
# ==========================================

from functools import partial
from tkinter import messagebox
import customtkinter as ctk

from functions.activity import get_activity
from functions.saved_apis import get_saved_APIs, remove_saved_API

BG_MAIN, BG_SIDEBAR, BG_CARD, BG_SURFACE = "#0B1020", "#111827", "#171F30", "#202B3D"
BORDER_COLOR, ACCENT_PRIMARY, ACCENT_HOVER, ACCENT_SECONDARY = "#283548", "#6366F1", "#4F46E5", "#38BDF8"
TEXT_MAIN, TEXT_MUTED = "#F8FAFC", "#94A3B8"
COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR = "#22C55E", "#F59E0B", "#EF4444"
FONT_FAMILY = "Inter"
METHOD_COLORS = {
    "GET": "#0284C7", "POST": "#16A34A", "PUT": "#D97706",
    "DELETE": "#DC2626", "PATCH": "#6366F1",
}


def wrap_long_text(text, max_chars):
    """Break overly long unbroken strings so labels wrap cleanly inside cards."""
    cleaned = str(text or "").replace("\r\n", "\n").strip()
    if not cleaned or max_chars < 12:
        return cleaned
    output_lines = []
    for line in cleaned.splitlines():
        words = line.split(" ")
        rebuilt = []
        for word in words:
            if len(word) <= max_chars:
                rebuilt.append(word)
                continue
            chunks = []
            while len(word) > max_chars:
                cut = word.rfind("/", 1, max_chars)
                if cut < max_chars // 3:
                    cut = max_chars
                else:
                    cut += 1
                chunks.append(word[:cut])
                word = word[cut:]
            if word:
                chunks.append(word)
            rebuilt.append("\n".join(chunks))
        output_lines.append(" ".join(rebuilt))
    return "\n".join(output_lines)


def add_text_card(parent, title, value, accent, avail_w, wrap_mode="word", max_height=160, mono=False):
    """Create a bordered detail card with an auto-sized, scrollable read-only text box."""
    card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
    card.pack(padx=6, pady=4, fill="x")
    ctk.CTkLabel(card, text=title, text_color=accent, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")).pack(padx=14, pady=(8, 4), anchor="w")

    cleaned = str(value or "").replace("\r\n", "\n").strip()
    if not cleaned or cleaned == "Not available":
        ctk.CTkLabel(card, text="Not available", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=14, pady=(0, 10), anchor="w")
        return card

    chars_per_line = max(28, int((avail_w - 24) / 7.4))
    total_lines = sum(max(1, (len(p) + chars_per_line - 1) // chars_per_line) for p in (cleaned.splitlines() or [""]))
    box_height = min(max_height, max(32, total_lines * 19 + 14))
    box = ctk.CTkTextbox(
        card, height=box_height, wrap=wrap_mode, fg_color=BG_SURFACE,
        text_color=TEXT_MAIN, border_width=0, corner_radius=5,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
    )
    box.pack(padx=12, pady=(0, 10), fill="x")
    box.insert("1.0", cleaned)
    box.configure(state="disabled")
    return card


def create_sidebar(window, callbacks):
    """Build the navigation sidebar and return its section buttons."""
    sidebar = ctk.CTkFrame(window, width=220, corner_radius=0, fg_color=BG_SIDEBAR)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    brand = ctk.CTkFrame(sidebar, fg_color="transparent")
    brand.pack(padx=18, pady=(22, 2), fill="x")
    ctk.CTkLabel(brand, text="●", text_color=ACCENT_PRIMARY, font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold")).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(brand, text="LOOKUPAPI", text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold")).pack(side="left")
    ctk.CTkLabel(sidebar, text="API Discovery Platform", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=11)).pack(padx=18, pady=(0, 18), anchor="w")
    ctk.CTkFrame(sidebar, height=1, fg_color=BORDER_COLOR).pack(padx=14, pady=(0, 14), fill="x")

    nav_buttons = {}
    for key, label_text, command in [
        ("home", "Home", callbacks["home"]),
        ("discover", "Discover APIs", callbacks["discover"]),
        ("saved", "My Saved APIs", callbacks["saved"]),
        ("activity", "Activity History", callbacks["activity"]),
    ]:
        btn = ctk.CTkButton(
            sidebar, text=f"  {label_text}", command=command, height=34, anchor="w",
            corner_radius=6, fg_color="transparent", hover_color=BG_CARD,
            text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        btn.pack(padx=12, pady=3, fill="x")
        nav_buttons[key] = btn

    # ==========================================
    # FINAL CODE
    # ==========================================
    if "test_apis" in callbacks:
        from ui.test_apis_screen import add_test_apis_nav_button
        add_test_apis_nav_button(sidebar, nav_buttons, callbacks["test_apis"])

    # ==========================================
    # MIDTERM CODE
    # ==========================================
    ctk.CTkButton(
        sidebar, text="Exit", command=callbacks["exit"], height=32,
        corner_radius=6, fg_color=BG_CARD, hover_color=COLOR_ERROR,
        border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MUTED,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
    ).pack(side="bottom", padx=12, pady=18, fill="x")
    return nav_buttons


def show_home_screen(content_frame, callbacks):
    """Display the home dashboard with overview cards and quick actions."""
    container = ctk.CTkFrame(content_frame, fg_color="transparent")
    container.pack(padx=28, pady=24, fill="both", expand=True)

    hero = ctk.CTkFrame(container, corner_radius=8, fg_color=BG_CARD, border_width=1, border_color=BORDER_COLOR)
    hero.pack(fill="x", pady=(0, 18))
    ctk.CTkLabel(hero, text="DEVELOPER WORKSPACE", text_color=ACCENT_SECONDARY, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")).pack(padx=24, pady=(20, 4), anchor="w")
    ctk.CTkLabel(hero, text="Welcome to LOOKUPAPI", text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold")).pack(padx=24, pady=(0, 6), anchor="w")
    desc_text = "Discover public REST APIs from APIs.guru, inspect OpenAPI specifications and HTTP endpoints, manage your saved API collection, and track activity logs."
    ctk.CTkLabel(hero, text=desc_text, text_color=TEXT_MUTED, wraplength=760, justify="left", font=ctk.CTkFont(family=FONT_FAMILY, size=13)).pack(padx=24, pady=(0, 16), anchor="w")

    cta_row = ctk.CTkFrame(hero, fg_color="transparent")
    cta_row.pack(padx=24, pady=(0, 20), fill="x")
    ctk.CTkButton(cta_row, text="Explore API Directory →", command=callbacks["discover"], height=34, width=180, corner_radius=6, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")).pack(side="left", padx=(0, 10))
    ctk.CTkButton(cta_row, text="View Saved APIs", command=callbacks["saved"], height=34, width=140, corner_radius=6, fg_color=BG_SURFACE, hover_color=BORDER_COLOR, text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=13)).pack(side="left")

    grid = ctk.CTkFrame(container, fg_color="transparent")
    grid.pack(fill="x", pady=(0, 16))
    grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

    saved_count = len(get_saved_APIs())
    activity_count = len([line for line in get_activity() if line.strip()])
    cards_data = [
        ("APIs.guru Catalog", "Discover APIs", "Search thousands of public APIs by name or provider and inspect endpoints.", "Open Directory", callbacks["discover"], ACCENT_SECONDARY),
        (f"{saved_count} Saved APIs", "Saved APIs", "Review your saved API collection, documentation links, and configuration details.", "Manage Saved", callbacks["saved"], ACCENT_PRIMARY),
        (f"{activity_count} Logged Events", "Activity History", "Audit timestamped API activity entries and status codes from your log file.", "View History", callbacks["activity"], COLOR_SUCCESS),
    ]

    for idx, (metric, card_title, card_desc, btn_text, cmd, accent) in enumerate(cards_data):
        card = ctk.CTkFrame(grid, corner_radius=8, fg_color=BG_CARD, border_width=1, border_color=BORDER_COLOR)
        padx = (0, 8) if idx == 0 else ((8, 0) if idx == 2 else 6)
        card.grid(row=0, column=idx, padx=padx, pady=4, sticky="nsew")
        ctk.CTkLabel(card, text=metric, text_color=accent, font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")).pack(padx=18, pady=(16, 4), anchor="w")
        ctk.CTkLabel(card, text=card_title, text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold")).pack(padx=18, pady=(0, 6), anchor="w")
        ctk.CTkLabel(card, text=card_desc, text_color=TEXT_MUTED, wraplength=240, justify="left", font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=18, pady=(0, 16), anchor="w")
        ctk.CTkButton(card, text=btn_text, command=cmd, height=30, corner_radius=6, fg_color=BG_SURFACE, hover_color=ACCENT_PRIMARY, text_color=TEXT_MAIN, font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")).pack(padx=18, pady=(0, 16), fill="x")


def display_saved_api_details(details_frame, state, api, status_label):
    """Show structured, wrapped details for the selected saved API."""
    state["selected_api"] = api
    for child in details_frame.winfo_children():
        child.destroy()
    if hasattr(details_frame, "_parent_canvas"):
        details_frame._parent_canvas.yview_moveto(0)

    details_frame.update_idletasks()
    panel_w = details_frame.winfo_width()
    avail_w = max(320, (panel_w if panel_w > 200 else 540) - 68)

    name = str(api.get("name") or "Not available").strip() or "Not available"
    category = str(api.get("category") or "Not available").strip() or "Not available"
    method = str(api.get("http_method") or "GET").strip().upper()
    auth_text = "Required" if api.get("requires_auth") else "No Auth"
    doc_url = str(api.get("documentation_url") or "").strip() or "Not available"
    endpoint_url = str(api.get("endpoint_url") or "").strip() or "Not available"
    description = str(api.get("description") or "").strip() or "Not available"

    overview = ctk.CTkFrame(details_frame, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
    overview.pack(padx=6, pady=(6, 6), fill="x")
    ctk.CTkLabel(overview, text="API OVERVIEW", text_color=ACCENT_SECONDARY, font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")).pack(padx=14, pady=(10, 2), anchor="w")
    ctk.CTkLabel(overview, text=wrap_long_text(name, max(24, avail_w // 10)), text_color=TEXT_MAIN, wraplength=avail_w, justify="left", anchor="w", font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold")).pack(padx=14, pady=(0, 8), fill="x")

    badges = ctk.CTkFrame(overview, fg_color="transparent")
    badges.pack(padx=14, pady=(0, 12), fill="x")
    ctk.CTkLabel(badges, text=f" {method} ", fg_color=METHOD_COLORS.get(method, ACCENT_PRIMARY), text_color=TEXT_MAIN, corner_radius=4, font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")).pack(side="left", padx=(0, 8))
    for pill_text in [f"Category: {category}", f"Auth: {auth_text}"]:
        ctk.CTkLabel(badges, text=f"  {pill_text}  ", fg_color=BG_SURFACE, text_color=TEXT_MUTED, corner_radius=4, wraplength=max(140, avail_w - 100), justify="left", font=ctk.CTkFont(family=FONT_FAMILY, size=11)).pack(side="left", padx=(0, 8))

    add_text_card(details_frame, "DOCUMENTATION LINK", doc_url, ACCENT_SECONDARY, avail_w, wrap_mode="char", max_height=76)
    add_text_card(details_frame, "ENDPOINT URL", endpoint_url, ACCENT_PRIMARY, avail_w, wrap_mode="char", max_height=76)
    add_text_card(details_frame, "DESCRIPTION", description, TEXT_MUTED, avail_w, wrap_mode="word", max_height=180)
    status_label.configure(text=f"Selected: {name[:60]}", text_color=ACCENT_SECONDARY)


def populate_saved_apis_list(list_frame, details_frame, state, status_label):
    """Load saved APIs and render them as selectable list buttons."""
    for child in list_frame.winfo_children():
        child.destroy()

    saved_apis = get_saved_APIs()
    if len(saved_apis) == 0:
        ctk.CTkLabel(list_frame, text="No saved APIs found.", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=10, pady=14, anchor="w")
        return

    for api in saved_apis:
        raw_name = str(api.get("name") or "Not available")
        short_name = raw_name if len(raw_name) <= 32 else raw_name[:29] + "..."
        cat = str(api.get("category") or "Not available")[:16]
        ctk.CTkButton(
            list_frame, text=f"{short_name}  ·  {cat}",
            command=partial(display_saved_api_details, details_frame, state, api, status_label),
            height=34, corner_radius=6, anchor="w", fg_color=BG_SURFACE,
            hover_color=ACCENT_PRIMARY, text_color=TEXT_MAIN,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        ).pack(padx=4, pady=3, fill="x")


def delete_selected_saved_api(list_frame, details_frame, state, status_label):
    """Confirm and delete the currently selected saved API, then refresh the list."""
    selected = state.get("selected_api")
    if not selected:
        status_label.configure(text="Please select a saved API first.", text_color=COLOR_WARNING)
        return

    api_name = selected.get("name") or "this API"
    api_id = selected.get("api_id")

    if not messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{api_name}'?"):
        status_label.configure(text="Removal cancelled.", text_color=TEXT_MUTED)
        return

    if remove_saved_API(api_id):
        state["selected_api"] = None
        for child in details_frame.winfo_children():
            child.destroy()
        ctk.CTkLabel(details_frame, text="Select a saved API on the left to inspect its details.", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=14, pady=18, anchor="w")
        status_label.configure(text=f"Removed '{api_name}' successfully.", text_color=COLOR_SUCCESS)
        populate_saved_apis_list(list_frame, details_frame, state, status_label)
    else:
        status_label.configure(text="Could not remove the selected API.", text_color=COLOR_ERROR)


def show_saved_apis_screen(content_frame, on_back):
    """Build and display the My Saved APIs section."""
    state = {"selected_api": None}

    header = ctk.CTkFrame(content_frame, fg_color="transparent")
    header.pack(padx=24, pady=(18, 10), fill="x")
    ctk.CTkLabel(header, text="My Saved APIs", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
    ctk.CTkButton(header, text="← Back to Home", command=on_back, width=120, height=30, corner_radius=6, fg_color=BG_CARD, hover_color=BG_SURFACE, border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="right")

    body = ctk.CTkFrame(content_frame, fg_color="transparent")
    body.pack(padx=24, pady=(0, 20), fill="both", expand=True)
    body.grid_columnconfigure(0, weight=1, uniform="split")
    body.grid_columnconfigure(1, weight=2, uniform="split")
    body.grid_rowconfigure(0, weight=1)

    list_frame = ctk.CTkScrollableFrame(body, label_text="Saved Collection", fg_color=BG_CARD, border_width=1, border_color=BORDER_COLOR, corner_radius=8, label_fg_color=BG_SURFACE, label_text_color=TEXT_MAIN)
    list_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

    right_panel = ctk.CTkFrame(body, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
    right_panel.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

    details_frame = ctk.CTkScrollableFrame(right_panel, fg_color=BG_MAIN, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
    details_frame.pack(padx=14, pady=(14, 8), fill="both", expand=True)
    ctk.CTkLabel(details_frame, text="Select a saved API on the left to inspect its details.", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(padx=14, pady=18, anchor="w")

    status_label = ctk.CTkLabel(right_panel, text="", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_MUTED)
    status_label.pack(padx=14, pady=(0, 6), anchor="w")

    actions_row = ctk.CTkFrame(right_panel, fg_color="transparent")
    actions_row.pack(padx=14, pady=(0, 14), fill="x")
    ctk.CTkButton(actions_row, text="Remove Saved API", height=32, corner_radius=6, command=partial(delete_selected_saved_api, list_frame, details_frame, state, status_label), fg_color=COLOR_ERROR, hover_color="#DC2626", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")).pack(side="left", padx=(0, 8))
    ctk.CTkButton(actions_row, text="Refresh List", height=32, corner_radius=6, command=partial(populate_saved_apis_list, list_frame, details_frame, state, status_label), fg_color=BG_SURFACE, hover_color=ACCENT_PRIMARY, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="left")

    populate_saved_apis_list(list_frame, details_frame, state, status_label)


def show_activity_screen(content_frame, on_back):
    """Build and display the Activity History log viewer."""
    header = ctk.CTkFrame(content_frame, fg_color="transparent")
    header.pack(padx=24, pady=(18, 10), fill="x")
    ctk.CTkLabel(header, text="Activity History", font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
    ctk.CTkButton(header, text="← Back to Home", command=on_back, width=120, height=30, corner_radius=6, fg_color=BG_CARD, hover_color=BG_SURFACE, border_width=1, border_color=BORDER_COLOR, text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_FAMILY, size=12)).pack(side="right")

    history_frame = ctk.CTkScrollableFrame(content_frame, label_text="Activity Log (Timestamp  |  API  |  Status  |  HTTP Code)", fg_color=BG_CARD, border_width=1, border_color=BORDER_COLOR, corner_radius=8, label_fg_color=BG_SURFACE, label_text_color=TEXT_MAIN)
    history_frame.pack(padx=24, pady=(0, 20), fill="both", expand=True)

    cleaned_lines = [line.strip() for line in get_activity() if line.strip()]
    if len(cleaned_lines) == 0:
        ctk.CTkLabel(history_frame, text="No activity history found.", font=ctk.CTkFont(family=FONT_FAMILY, size=13), text_color=TEXT_MUTED).pack(padx=14, pady=16, anchor="w")
        return

    for entry in reversed(cleaned_lines):
        row = ctk.CTkFrame(history_frame, fg_color=BG_SURFACE, corner_radius=6)
        row.pack(padx=6, pady=3, fill="x")
        color = COLOR_SUCCESS if "Success" in entry else (COLOR_ERROR if "Failed" in entry else TEXT_MAIN)
        ctk.CTkLabel(row, text=entry, font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=color, anchor="w", justify="left", wraplength=780).pack(padx=12, pady=7, fill="x")
