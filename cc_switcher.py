import customtkinter as ctk
import os
import shutil
import json
import requests
import tkinter.messagebox as messagebox
import tkinter.font as tkfont
from pathlib import Path
from typing import Dict, List, Optional, Any

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Modern card-style color schemes
DARK_COLORS = {
    "bg_primary": "#1a1a1a",  # Dark background
    "bg_secondary": "#2b2b2b",  # Card background
    "bg_tertiary": "#333333",  # Elevated card background
    "card_hover": "#3a3a3a",  # Card hover state
    "border": "#404040",  # Subtle border
    "shadow": "#000000",  # Card shadow
    "text_primary": "#ffffff",  # Primary text
    "text_secondary": "#b3b3b3",  # Secondary text
    "text_muted": "#666666",  # Muted text
    "accent_primary": "#4a90e2",  # Softer blue accent
    "accent_hover": "#357abd",  # Softer blue hover
    "accent_red": "#ff6b6b",  # Error/active state
    "accent_red_hover": "#ff5252",  # Error hover
    "success_green": "#4caf50",  # Success state
    "warning_orange": "#ff9800",  # Warning state
}

LIGHT_COLORS = {
    "bg_primary": "#f8f8f6",  # Warm, eye-friendly background
    "bg_secondary": "#fefffe",  # Soft white with warm undertone
    "bg_tertiary": "#f3f4f2",  # Elevated background with subtle contrast
    "card_hover": "#eef1ee",  # Gentle hover effect
    "border": "#d0d7de",  # Professional border color
    "shadow": "#eaeef2",  # Soft shadow color
    "text_primary": "#24292f",  # High contrast primary text
    "text_secondary": "#57606a",  # Well-balanced secondary text
    "text_muted": "#8c959f",  # Properly muted text
    "accent_primary": "#5a9fd4",  # Softer, more elegant blue
    "accent_hover": "#4a8bc2",  # Corresponding softer hover
    "accent_red": "#d1242f",  # Professional red for errors/active
    "accent_red_hover": "#cf222e",  # Corresponding hover state
    "success_green": "#1a7f37",  # Professional success green
    "warning_orange": "#d97916",  # Balanced warning orange
}

# Default to dark theme
COLORS = DARK_COLORS


class ClaudeConfigSwitcher:
    def __init__(self):
        self.root = ctk.CTk()
        # Configure window properties
        self.root.configure(fg_color=COLORS["bg_primary"])
        self.root.title("CC 配置切换器")

        # Keep system window but make it resizable and with proper taskbar behavior
        self.root.resizable(True, True)

        # Set initial size
        window_width = 900
        window_height = 430

        # Get screen dimensions and center the window
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int((screen_width - window_width) // 2)
        center_y = int((screen_height - window_height) // 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.claude_dir = Path.home() / ".claude"
        self.settings_file = self.claude_dir / "settings.json"
        self.app_state_file = self.claude_dir / ".cc-cache"
        self.configs_file = self.claude_dir / "cc_switcher_configs.json"

        self.config_files = []
        self.current_config = None
        self.configs_data = self.load_configs_data()
        self.current_config_name = None

        # Initialize theme from saved state
        self.init_theme()

        # Setup fonts for better Chinese support
        self.setup_fonts()

        # Initialize UI after all variables are set
        self.setup_ui()

        # Apply theme colors after UI is created
        if ctk.get_appearance_mode() == "Light":
            self.apply_theme_colors()

        # Use after_idle to ensure UI is ready before refreshing
        self.root.after_idle(lambda: self.refresh_config_list(is_initial=True))
        self.root.after_idle(lambda: self.refresh_managed_configs())

    def init_theme(self):
        """Initialize theme from saved state"""
        global COLORS
        app_state = self.load_app_state()
        saved_theme = app_state.get('theme_mode', 'dark')

        if saved_theme == 'light':
            ctk.set_appearance_mode("light")
            COLORS = LIGHT_COLORS
        else:
            ctk.set_appearance_mode("dark")
            COLORS = DARK_COLORS

    def load_app_state(self):
        """Load the last selected file and theme from app state"""
        try:
            if self.app_state_file.exists():
                with open(self.app_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return {
                        'last_selected_file': state.get('last_selected_file'),
                        'theme_mode': state.get('theme_mode', 'dark'),
                    }
        except (json.JSONDecodeError, IOError):
            pass
        return {'last_selected_file': None, 'theme_mode': 'dark'}

    def save_app_state(self, selected_file_name=None, theme_mode=None):
        """Save the current selected file and theme to app state"""
        try:
            self.claude_dir.mkdir(exist_ok=True)

            # Load existing state
            state = {'last_selected_file': None, 'theme_mode': 'dark'}
            if self.app_state_file.exists():
                try:
                    with open(self.app_state_file, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

            # Update with new values if provided
            if selected_file_name is not None:
                state['last_selected_file'] = selected_file_name
            if theme_mode is not None:
                state['theme_mode'] = theme_mode

            with open(self.app_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except (IOError, OSError):
            pass  # Silently ignore save failures

    def setup_fonts(self):
        """Setup fonts with better Chinese character support"""
        # Define font families in order of preference
        self.chinese_fonts = [
            "Microsoft YaHei UI",  # Windows 10/11 preferred
            "Microsoft YaHei",     # Windows general
            "PingFang SC",         # macOS preferred
            "PingFang HK",         # macOS Hong Kong
            "PingFang TC",         # macOS Taiwan
            "Noto Sans CJK SC",    # Linux/macOS
            "Noto Sans CJK TC",    # Linux/macOS
            "Source Han Sans SC",  # Linux/macOS
            "Source Han Sans TC",  # Linux/macOS
            "SimSun",             # Windows fallback
            "SimHei",             # Windows fallback
            "KaiTi",              # Windows fallback
            "FangSong",           # Windows fallback
            "Arial Unicode MS",   # Cross-platform fallback
            "Segoe UI",           # Default Windows font
            "Arial",              # Universal fallback
            "Helvetica",          # Universal fallback
        ]

        # Find the best available Chinese font
        self.best_chinese_font = self.find_best_font()

    def find_best_font(self):
        """Find the best available Chinese font"""
        # Simple approach - try the most common Windows Chinese fonts first
        try:
            # Check for Microsoft YaHei UI (Windows 10/11 default)
            ctk.CTkFont(family="Microsoft YaHei UI", size=10)
            return "Microsoft YaHei UI"
        except:
            pass

        try:
            # Check for Microsoft YaHei (Windows general)
            ctk.CTkFont(family="Microsoft YaHei", size=10)
            return "Microsoft YaHei"
        except:
            pass

        try:
            # Check for SimSun (Windows fallback)
            ctk.CTkFont(family="SimSun", size=10)
            return "SimSun"
        except:
            pass

        # Fallback to default
        return "Segoe UI"

    def get_font(self, size=12, weight="normal"):
        """Get a font with Chinese support"""
        weight_map = {
            "normal": "normal",
            "bold": "bold"
        }
        ctk_weight = weight_map.get(weight, "normal")

        return ctk.CTkFont(
            family=self.best_chinese_font,
            size=size,
            weight=ctk_weight
        )

    def setup_ui(self):
        # --- Main Content Area ---
        content_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # --- Toolbar (leftmost panel) ---
        self.toolbar = ctk.CTkFrame(content_frame, width=30, corner_radius=0, fg_color=COLORS["bg_secondary"])
        self.toolbar.pack(side="left", fill="y", pady=0, padx=(0, 0.5))
        self.toolbar.pack_propagate(False)

        # --- Toolbar Content ---
        toolbar_container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        toolbar_container.pack(fill="both", expand=True, padx=2, pady=8)

        # Top button container for sync button
        top_container = ctk.CTkFrame(toolbar_container, fg_color="transparent")
        top_container.pack(side="top")

        # WebDAV sync button (sun behind cloud icon) - at the very top
        self.sync_btn = ctk.CTkButton(
            top_container,
            text="🌥",
            command=self.webdav_sync,
            width=26,
            height=26,
            corner_radius=0,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            border_width=0,
        )
        self.sync_btn.pack(pady=(0, 8))

        # Bottom button container to push buttons to bottom
        button_container = ctk.CTkFrame(toolbar_container, fg_color="transparent")
        button_container.pack(side="bottom")

        # Settings button (gear icon) - at the very bottom
        self.settings_btn = ctk.CTkButton(
            button_container,
            text="⚙",
            command=self.open_settings,
            width=26,
            height=26,
            corner_radius=0,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            border_width=0,
        )
        self.settings_btn.pack(side="bottom", pady=(4, 0))

        # Theme toggle button (sun/moon icon) - above settings
        initial_theme_icon = "☀" if ctk.get_appearance_mode() == "Light" else "🌙"
        self.theme_btn = ctk.CTkButton(
            button_container,
            text=initial_theme_icon,
            command=self.toggle_theme,
            width=26,
            height=26,
            corner_radius=0,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            border_width=0,
        )
        self.theme_btn.pack(side="bottom", pady=(0, 4))

        # --- Left Panel ---
        self.left_panel = ctk.CTkFrame(content_frame, width=260, corner_radius=0, fg_color=COLORS["bg_secondary"])
        self.left_panel.pack(side="left", fill="y", pady=0, padx=(1, 1))
        self.left_panel.pack_propagate(False)

        # --- Bottom Controls Container ---
        bottom_container = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        bottom_container.pack(side="bottom", fill="x", padx=8, pady=(4, 8))

        # --- Status Label ---
        self.status_label = ctk.CTkLabel(
            bottom_container,
            text="",
            font=self.get_font(size=14),
            height=20,
            text_color=COLORS["text_muted"],
        )
        self.status_label.pack(pady=(0, 4), padx=0, fill="x")

        # --- Action Buttons ---
        self.switch_btn = ctk.CTkButton(
            bottom_container,
            text="切换配置",
            command=self.switch_config,
            height=30,
            font=self.get_font(size=13, weight="bold"),
            corner_radius=0,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.switch_btn.pack(pady=(0, 4), padx=0, fill="x")

        # Button row for secondary actions
        button_row = ctk.CTkFrame(bottom_container, fg_color="transparent")
        button_row.pack(fill="x", pady=0)

        self.config_manager_btn = ctk.CTkButton(
            button_row,
            text="配置管理",
            command=self.open_config_manager,
            height=30,
            corner_radius=0,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=self.get_font(size=13),
        )
        self.config_manager_btn.pack(fill="x", pady=(0, 4))

        self.api_test_btn = ctk.CTkButton(
            button_row,
            text="API 测试",
            command=self.open_api_test,
            height=30,
            corner_radius=0,
            fg_color=COLORS["warning_orange"],
            hover_color="#e68900",
            text_color="white",
            font=self.get_font(size=13),
        )
        self.api_test_btn.pack(fill="x", pady=(0, 4))

        # Second button row
        button_row2 = ctk.CTkFrame(bottom_container, fg_color="transparent")
        button_row2.pack(fill="x", pady=0)

        self.refresh_btn = ctk.CTkButton(
            button_row2,
            text="刷新",
            command=self.refresh_config_list,
            height=30,
            corner_radius=0,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            font=self.get_font(size=13),
            border_width=1,
            border_color=COLORS["border"],
        )
        self.refresh_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.open_dir_btn = ctk.CTkButton(
            button_row2,
            text="打开目录",
            command=self.open_config_directory,
            height=30,
            corner_radius=0,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            font=self.get_font(size=13),
            border_width=1,
            border_color=COLORS["border"],
        )
        self.open_dir_btn.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # --- Config List (takes all remaining space) ---
        list_container = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        list_container.pack(fill="both", expand=True, padx=8, pady=8)

        # Tab-like headers
        header_container = ctk.CTkFrame(list_container, fg_color="transparent")
        header_container.pack(fill="x", pady=(0, 5))

        # Files tab
        self.files_tab_btn = ctk.CTkButton(
            header_container,
            text="配置文件",
            command=lambda: self.switch_tab("files"),
            height=25,
            corner_radius=8,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=self.get_font(size=11, weight="bold"),
        )
        self.files_tab_btn.pack(side="left", fill="x", expand=True)

        # Configurations tab
        self.configs_tab_btn = ctk.CTkButton(
            header_container,
            text="管理配置",
            command=lambda: self.switch_tab("configs"),
            height=25,
            corner_radius=8,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            font=self.get_font(size=11),
        )
        self.configs_tab_btn.pack(side="right", fill="x", expand=True)

        # Content area
        content_container = ctk.CTkFrame(list_container, fg_color=COLORS["bg_tertiary"])
        content_container.pack(fill="both", expand=True)

        # Files list (original config list)
        self.files_frame = ctk.CTkFrame(content_container, corner_radius=0, fg_color="transparent")
        self.files_frame.pack(fill="both", expand=True)

        self.config_listbox = ctk.CTkFrame(self.files_frame, corner_radius=0, fg_color="transparent")
        self.config_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Managed configs list
        self.configs_frame = ctk.CTkFrame(content_container, corner_radius=0, fg_color="transparent")

        self.managed_configs_list = ctk.CTkScrollableFrame(self.configs_frame, fg_color="transparent")
        self.managed_configs_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Current active tab
        self.active_tab = "files"

        # --- Right Panel (Preview) ---
        self.right_panel = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=COLORS["bg_secondary"])
        self.right_panel.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=0)

        # Preview content
        preview_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        preview_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.preview_textbox = ctk.CTkTextbox(
            preview_container,
            corner_radius=0,
            font=self.get_font(size=13),
            wrap="word",
            fg_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.preview_textbox.pack(fill="both", expand=True)

        self.selected_config = None

    def create_config_button(self, config_file, settings_content):
        # Card container with modern styling
        card = ctk.CTkFrame(
            self.config_listbox,
            height=30,
            corner_radius=0,
            fg_color=COLORS["bg_tertiary"],
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=(0, 1), padx=0)
        card.pack_propagate(False)

        # Main content frame
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # File name with compact typography
        name_label = ctk.CTkLabel(
            content_frame,
            text=config_file.name,
            font=self.get_font(size=13),
            anchor="w",
            text_color=COLORS["text_primary"],
        )
        name_label.pack(side="left", fill="x", expand=True, anchor="w")

        # Status indicator with modern styling
        is_active = config_file.name == "settings.json"
        is_synced = False

        if not is_active and settings_content is not None:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    current_content = json.load(f)
                if current_content == settings_content:
                    is_synced = True
            except (json.JSONDecodeError, IOError):
                pass

        if is_active:
            status_label = ctk.CTkLabel(
                content_frame,
                text="●",
                font=self.get_font(size=15, weight="bold"),
                text_color=COLORS["accent_red"],
            )
            status_label.pack(side="right", padx=(6, 0))
        elif is_synced:
            status_label = ctk.CTkLabel(
                content_frame,
                text="●",
                font=self.get_font(size=15, weight="bold"),
                text_color=COLORS["success_green"],
            )
            status_label.pack(side="right", padx=(6, 0))

        # Add hover effect data
        card._config_file = config_file
        card._is_selected = False

        # Bind click and hover events to all components
        def on_click(e):
            self.select_config(config_file)

        def on_double_click(e):
            self.select_config(config_file)
            self.switch_config()

        def on_enter(e):
            if not card._is_selected:
                card.configure(fg_color=COLORS["card_hover"])

        def on_leave(e):
            if not card._is_selected:
                card.configure(fg_color=COLORS["bg_tertiary"])

        # Bind events to all widgets to prevent flickering
        widgets_to_bind = [card, content_frame, name_label]
        if 'status_label' in locals():
            widgets_to_bind.append(status_label)

        for widget in widgets_to_bind:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Double-Button-1>", on_double_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def select_config(self, config_file):
        self.selected_config = config_file

        # Save the selected file to app state
        self.save_app_state(selected_file_name=config_file.name)

        # Update UI selection highlight
        for child in self.config_listbox.winfo_children():
            if hasattr(child, '_config_file'):
                if child._config_file.name == config_file.name:
                    # Selected card - no border for clean look
                    child.configure(fg_color=COLORS["accent_primary"], border_width=0)
                    child._is_selected = True
                    # Update text color for better contrast on blue background
                    for widget in child.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):  # content_frame
                            for label in widget.winfo_children():
                                if isinstance(label, ctk.CTkLabel) and "settings" in label.cget("text"):
                                    label.configure(text_color="white")
                else:
                    # Unselected cards - restore border
                    child.configure(fg_color=COLORS["bg_tertiary"], border_width=1, border_color=COLORS["border"])
                    child._is_selected = False
                    # Restore original text color
                    for widget in child.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):  # content_frame
                            for label in widget.winfo_children():
                                if isinstance(label, ctk.CTkLabel) and "settings" in label.cget("text"):
                                    label.configure(text_color=COLORS["text_primary"])

        self.update_preview(config_file)

    def update_preview(self, config_file):
        try:
            self.preview_textbox.delete("1.0", "end")

            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    json_data = json.loads(content)
                    formatted_content = json.dumps(json_data, indent=2, ensure_ascii=False)
                    self.insert_json_with_highlighting(formatted_content)
                except json.JSONDecodeError:
                    self.preview_textbox.insert("1.0", content)

        except Exception:
            self.update_status("Error reading file", COLORS["accent_red"])

    def insert_json_with_highlighting(self, json_content):
        """Insert JSON content with syntax highlighting"""
        import re

        # Define color scheme for JSON syntax highlighting based on current theme
        self.update_json_highlighting_colors()

        # Insert the content
        self.preview_textbox.insert("1.0", json_content)

        # Apply highlighting using regex patterns
        content = json_content

        # Keep track of string positions to avoid re-highlighting them
        string_ranges = []

        # First pass: Highlight strings (including keys and values)
        for match in re.finditer(r'"([^"\\\\]|\\\\.)*"', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            string_ranges.append((match.start(), match.end()))

            # Check if this string is a key (followed by colon)
            rest_content = content[match.end() :].lstrip()
            if rest_content.startswith(':'):
                self.preview_textbox.tag_add("key", start_idx, end_idx)
            else:
                self.preview_textbox.tag_add("string", start_idx, end_idx)

        # Helper function to check if position is inside a string
        def is_in_string(pos):
            for start, end in string_ranges:
                if start <= pos < end:
                    return True
            return False

        # Highlight numbers (only outside strings)
        for match in re.finditer(r'-?\d+\.?\d*([eE][+-]?\d+)?', content):
            if not is_in_string(match.start()):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.preview_textbox.tag_add("number", start_idx, end_idx)

        # Highlight booleans and null (only outside strings)
        for match in re.finditer(r'\b(true|false|null)\b', content):
            if not is_in_string(match.start()):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                if match.group(1) in ['true', 'false']:
                    self.preview_textbox.tag_add("boolean", start_idx, end_idx)
                else:
                    self.preview_textbox.tag_add("null", start_idx, end_idx)

        # Highlight braces and brackets (only outside strings)
        for match in re.finditer(r'[{}]', content):
            if not is_in_string(match.start()):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.preview_textbox.tag_add("brace", start_idx, end_idx)

        for match in re.finditer(r'[\[\]]', content):
            if not is_in_string(match.start()):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.preview_textbox.tag_add("bracket", start_idx, end_idx)

        # Highlight colons and commas (only outside strings)
        for match in re.finditer(r':', content):
            if not is_in_string(match.start()):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.preview_textbox.tag_add("colon", start_idx, end_idx)

        for match in re.finditer(r',', content):
            if not is_in_string(match.start()):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.preview_textbox.tag_add("comma", start_idx, end_idx)

    def switch_config(self):
        if not self.selected_config:
            self.update_status("请先选择一个配置", COLORS["accent_red"])
            return

        if self.selected_config.name == "settings.json":
            self.update_status("已经是当前活跃的配置", COLORS["text_muted"])
            return

        if not self.selected_config.exists():
            self.update_status("文件未找到", COLORS["accent_red"])
            return

        try:
            shutil.copy2(self.selected_config, self.settings_file)
            self.update_status(f"已切换到 {self.selected_config.name}", COLORS["success_green"])
            self.refresh_config_list()

        except Exception:
            self.update_status("切换失败", COLORS["accent_red"])

    def open_config_directory(self):
        try:
            os.startfile(self.claude_dir)
        except Exception:
            self.update_status("打开目录失败", COLORS["accent_red"])

    def update_status(self, message, color=None):
        if color is None:
            color = COLORS["text_muted"]
        self.status_label.configure(text=message, text_color=color)
        # Clear the message after 4 seconds
        self.root.after(4000, lambda: self.status_label.configure(text=""))

    def refresh_config_list(self, is_initial=False):
        try:
            # Remember current selection (only for non-initial refresh)
            current_selection = self.selected_config if not is_initial else None

            # Clear existing list
            for widget in self.config_listbox.winfo_children():
                widget.destroy()

            self.config_files = []
            self.selected_config = None

            if not self.claude_dir.exists():
                self.update_status("目录未找到", COLORS["accent_red"])
                return

            # Get content of settings.json for comparison
            settings_content = None
            if self.settings_file.exists():
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        settings_content = json.load(f)
                except (json.JSONDecodeError, IOError):
                    settings_content = None  # Mark as not readable

            # Scan for settings-related config files and sort them with settings.json on top
            other_files = []
            settings_file_path = None
            for file_path in self.claude_dir.glob("*.json"):
                file_name = file_path.name.lower()
                # Filter to only include settings-related files
                if (
                    file_name == "settings.json"
                    or "settings" in file_name
                    or file_name.startswith("settings_")
                    or file_name.endswith("_settings.json")
                ):
                    if file_path.name == "settings.json":
                        settings_file_path = file_path
                    else:
                        other_files.append(file_path)

            other_files.sort()

            if settings_file_path:
                self.config_files.append(settings_file_path)
            self.config_files.extend(other_files)

            # Create config buttons
            for config_file in self.config_files:
                self.create_config_button(config_file, settings_content)

            if is_initial:
                # Initial load: Restore last selection or default to settings.json
                app_state = self.load_app_state()
                last_selected = app_state.get('last_selected_file')
                target_file = None

                # Try to find the last selected file
                if last_selected:
                    for config_file in self.config_files:
                        if config_file.name == last_selected:
                            target_file = config_file
                            break

                # If no last selection or file not found, default to settings.json
                if not target_file and settings_file_path:
                    target_file = settings_file_path

                # Select the target file if found
                if target_file:
                    self.select_config(target_file)
            else:
                # Regular refresh: Restore selection if the file still exists
                if current_selection and current_selection.exists():
                    # Find the corresponding file in the new list
                    for config_file in self.config_files:
                        if config_file.name == current_selection.name:
                            self.select_config(config_file)
                            break

        except Exception as e:
            self.update_status(f"加载配置错误: {str(e)}", COLORS["accent_red"])

    def switch_tab(self, tab_name):
        """Switch between files and configurations tabs"""
        self.active_tab = tab_name

        if tab_name == "files":
            # Show files tab, hide configs tab
            self.files_frame.pack(fill="both", expand=True)
            self.configs_frame.pack_forget()

            # Update tab buttons
            self.files_tab_btn.configure(
                fg_color=COLORS["accent_primary"],
                text_color="white",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
            )
            self.configs_tab_btn.configure(
                fg_color=COLORS["bg_tertiary"],
                text_color=COLORS["text_primary"],
                font=ctk.CTkFont(family="Segoe UI", size=11)
            )

            # Update action buttons
            self.switch_btn.configure(text="切换配置", command=self.switch_config)
            self.config_manager_btn.configure(state="normal")

        else:  # configs
            # Show configs tab, hide files tab
            self.configs_frame.pack(fill="both", expand=True)
            self.files_frame.pack_forget()

            # Update tab buttons
            self.configs_tab_btn.configure(
                fg_color=COLORS["accent_primary"],
                text_color="white",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
            )
            self.files_tab_btn.configure(
                fg_color=COLORS["bg_tertiary"],
                text_color=COLORS["text_primary"],
                font=ctk.CTkFont(family="Segoe UI", size=11)
            )

            # Update action buttons
            self.switch_btn.configure(text="切换至配置", command=self.switch_to_selected_config)
            self.config_manager_btn.configure(state="normal")

    def refresh_managed_configs(self):
        """Refresh the managed configurations list"""
        # Clear existing items
        for widget in self.managed_configs_list.winfo_children():
            widget.destroy()

        # Add managed config items
        for config in self.configs_data["configs"]:
            self.create_managed_config_item(config)

    def create_managed_config_item(self, config):
        """Create a managed configuration item"""
        item_frame = ctk.CTkFrame(self.managed_configs_list, fg_color=COLORS["bg_primary"])
        item_frame.pack(fill="x", pady=2, padx=2)

        # Config content
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=8)

        # Header with name and status
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x")

        # Config name
        name_label = ctk.CTkLabel(
            header_frame,
            text=config["name"],
            font=self.get_font(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        name_label.pack(side="left")

        # Active indicator
        if config["name"] == self.configs_data.get("active_config"):
            active_label = ctk.CTkLabel(
                header_frame,
                text="活跃",
                font=self.get_font(size=10, weight="bold"),
                text_color="white",
                fg_color=COLORS["success_green"],
                corner_radius=3
            )
            active_label.pack(side="right", padx=(0, 5))

        # Model and URL info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(5, 0))

        model_label = ctk.CTkLabel(
            info_frame,
            text=f"模型: {config['default_model']}",
            font=self.get_font(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        model_label.pack(anchor="w")

        # Truncate URL if too long
        url = config["ANTHROPIC_BASE_URL"]
        if len(url) > 35:
            url = url[:32] + "..."

        url_label = ctk.CTkLabel(
            info_frame,
            text=f"URL: {url}",
            font=self.get_font(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        url_label.pack(anchor="w")

        # Click handlers
        def on_click(event, cfg=config):
            self.select_managed_config(cfg)

        def on_double_click(event, cfg=config):
            self.select_managed_config(cfg)
            self.switch_to_selected_config()

        # Bind events
        widgets_to_bind = [item_frame, content_frame, header_frame, name_label, info_frame, model_label, url_label]
        for widget in widgets_to_bind:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Double-Button-1>", on_double_click)

        # Store reference for selection
        item_frame._config_data = config
        item_frame._is_selected = False

        # Add hover effects
        def on_enter(e):
            if not item_frame._is_selected:
                item_frame.configure(fg_color=COLORS["card_hover"])

        def on_leave(e):
            if not item_frame._is_selected:
                item_frame.configure(fg_color=COLORS["bg_primary"])

        for widget in widgets_to_bind:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def select_managed_config(self, config):
        """Select a managed configuration"""
        self.selected_managed_config = config

        # Update visual selection
        for widget in self.managed_configs_list.winfo_children():
            if hasattr(widget, '_config_data'):
                if widget._config_data["name"] == config["name"]:
                    widget.configure(fg_color=COLORS["accent_primary"])
                    widget._is_selected = True
                else:
                    widget.configure(fg_color=COLORS["bg_primary"])
                    widget._is_selected = False

        # Update preview with config details
        self.update_managed_config_preview(config)

    def update_managed_config_preview(self, config):
        """Update preview with managed config details"""
        try:
            self.preview_textbox.delete("1.0", "end")

            # Create a formatted view of the config
            preview_data = {
                "配置名称": config["name"],
                "基础URL": config["ANTHROPIC_BASE_URL"],
                "认证令牌": "***" + config["ANTHROPIC_AUTH_TOKEN"][-6:] if len(config["ANTHROPIC_AUTH_TOKEN"]) > 6 else "***",
                "默认模型": config["default_model"],
                "状态": "活跃" if config["name"] == self.configs_data.get("active_config") else "非活跃"
            }

            formatted_content = json.dumps(preview_data, indent=2, ensure_ascii=False)
            self.insert_json_with_highlighting(formatted_content)

        except Exception:
            self.update_status("更新预览错误", COLORS["accent_red"])

    def switch_to_selected_config(self):
        """Switch to the selected managed configuration"""
        if self.active_tab != "configs":
            self.update_status("请从“管理配置”标签页选择一个配置", COLORS["accent_red"])
            return

        if not hasattr(self, 'selected_managed_config') or not self.selected_managed_config:
            self.update_status("请先选择一个配置", COLORS["accent_red"])
            return

        name = self.selected_managed_config["name"]
        if self.switch_to_config(name):
            self.update_status(f"已切换到配置 '{name}'", COLORS["success_green"])
            self.refresh_config_list()
            self.refresh_managed_configs()
        else:
            self.update_status("切换配置失败", COLORS["accent_red"])

    def run(self):
        self.root.mainloop()

    def open_settings(self):
        """Open config management dialog"""
        self.open_config_manager()

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        global COLORS
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("light")
            COLORS = LIGHT_COLORS
            self.theme_btn.configure(text="☀")
            self.save_app_state(theme_mode="light")
            self.update_status("Switched to light theme", COLORS["success_green"])
        else:
            ctk.set_appearance_mode("dark")
            COLORS = DARK_COLORS
            self.theme_btn.configure(text="🌙")
            self.save_app_state(theme_mode="dark")
            self.update_status("Switched to dark theme", COLORS["success_green"])

        # Refresh the UI with new colors
        self.apply_theme_colors()

    def apply_theme_colors(self):
        """Apply current theme colors to all UI components"""
        # Update main window
        self.root.configure(fg_color=COLORS["bg_primary"])

        # Update toolbar
        self.toolbar.configure(fg_color=COLORS["bg_secondary"])

        # Update toolbar buttons
        toolbar_buttons = [self.sync_btn, self.theme_btn, self.settings_btn]
        for btn in toolbar_buttons:
            btn.configure(hover_color=COLORS["card_hover"], text_color=COLORS["text_primary"])

        # Update left panel
        self.left_panel.configure(fg_color=COLORS["bg_secondary"])

        # Update status label
        self.status_label.configure(text_color=COLORS["text_muted"])

        # Update action buttons
        action_buttons = [self.switch_btn, self.refresh_btn, self.open_dir_btn, self.config_manager_btn, self.api_test_btn]
        for btn in action_buttons:
            if btn == self.config_manager_btn:
                btn.configure(
                    fg_color=COLORS["accent_primary"],
                    hover_color=COLORS["accent_hover"],
                    text_color="white"
                )
            elif btn == self.api_test_btn:
                btn.configure(
                    fg_color=COLORS["warning_orange"],
                    hover_color="#e68900",
                    text_color="white"
                )
            else:
                btn.configure(
                    fg_color=COLORS["bg_tertiary"],
                    hover_color=COLORS["card_hover"],
                    text_color=COLORS["text_primary"],
                    border_color=COLORS["border"],
                )

        # Update tab buttons
        if hasattr(self, 'files_tab_btn'):
            if self.active_tab == "files":
                self.files_tab_btn.configure(
                    fg_color=COLORS["accent_primary"],
                    hover_color=COLORS["accent_hover"],
                    text_color="white"
                )
                self.configs_tab_btn.configure(
                    fg_color=COLORS["bg_tertiary"],
                    hover_color=COLORS["card_hover"],
                    text_color=COLORS["text_primary"]
                )
            else:
                self.configs_tab_btn.configure(
                    fg_color=COLORS["accent_primary"],
                    hover_color=COLORS["accent_hover"],
                    text_color="white"
                )
                self.files_tab_btn.configure(
                    fg_color=COLORS["bg_tertiary"],
                    hover_color=COLORS["card_hover"],
                    text_color=COLORS["text_primary"]
                )

        # Update right panel
        self.right_panel.configure(fg_color=COLORS["bg_secondary"])

        # Update preview textbox
        self.preview_textbox.configure(
            fg_color=COLORS["bg_tertiary"], text_color=COLORS["text_primary"], border_color=COLORS["border"]
        )

        # Update JSON syntax highlighting colors for current theme
        if hasattr(self, 'preview_textbox'):
            self.update_json_highlighting_colors()

        # Refresh config list to apply new colors
        self.refresh_config_list()
        self.refresh_managed_configs()

    def update_json_highlighting_colors(self):
        """Update JSON syntax highlighting colors based on current theme"""
        if ctk.get_appearance_mode() == "Light":
            # Light theme colors
            colors = {
                "string": "#d14",  # Red for strings
                "number": "#099",  # Teal for numbers
                "boolean": "#0086b3",  # Blue for booleans
                "null": "#0086b3",  # Blue for null
                "key": "#0086b3",  # Blue for keys
                "brace": "#333",  # Dark gray for braces
                "bracket": "#333",  # Dark gray for brackets
                "colon": "#333",  # Dark gray for colons
                "comma": "#333",  # Dark gray for commas
            }
        else:
            # Dark theme colors (original)
            colors = {
                "string": "#ce9178",  # Orange for strings
                "number": "#b5cea8",  # Light green for numbers
                "boolean": "#569cd6",  # Blue for booleans
                "null": "#569cd6",  # Blue for null
                "key": "#9cdcfe",  # Light blue for keys
                "brace": "#ffd700",  # Gold for braces
                "bracket": "#ffd700",  # Gold for brackets
                "colon": "#ffffff",  # White for colons
                "comma": "#ffffff",  # White for commas
            }

        # Configure text tags for highlighting
        for tag, color in colors.items():
            self.preview_textbox.tag_config(tag, foreground=color)

    def webdav_sync(self):
        """WebDAV synchronization functionality"""
        self.update_status("WebDAV sync feature coming soon", COLORS["text_muted"])

    # Configuration Management Methods
    def load_configs_data(self) -> Dict[str, Any]:
        """Load configurations from JSON file"""
        default_data = {
            "configs": [],
            "active_config": None,
            "version": "1.0"
        }

        if not self.configs_file.exists():
            return default_data

        try:
            with open(self.configs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all required fields exist
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                return data
        except (json.JSONDecodeError, IOError):
            return default_data

    def save_configs_data(self):
        """Save configurations to JSON file"""
        try:
            self.claude_dir.mkdir(exist_ok=True)
            with open(self.configs_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs_data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            self.update_status(f"保存配置失败: {str(e)}", COLORS["accent_red"])

    def get_available_models(self) -> List[str]:
        """Get list of available Claude models"""
        return [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229"
        ]

    def test_config(self, base_url: str, auth_token: str, model: str) -> tuple[bool, str]:
        """Test if a configuration is valid by making a test API call - Full Claude Code CLI compatibility"""
        try:
            # Use exact Claude Code CLI headers from actual implementation
            headers = {
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": auth_token,
                "user-agent": "claude-cli/1.0.115 (external, cli)",
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br"
            }

            data = {
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "1+2=?"}]
            }

            url = f"{base_url.rstrip('/')}/v1/messages"

            # Use requests.Session for better connection handling like Claude Code
            session = requests.Session()
            session.headers.update(headers)

            # Remove debug output for normal operation
            # print(f"Config Test Debug:")
            # print(f"URL: {url}")
            # print(f"Headers: {dict(session.headers)}")
            # print(f"Data: {data}")

            response = session.post(url, json=data, timeout=10)

            print(f"Response Status: {response.status_code}")
            print(f"Response Text: {response.text}")

            if response.status_code == 200:
                return True, "配置有效"
            elif response.status_code == 401:
                return False, "无效的认证令牌"
            elif response.status_code == 404:
                return False, "无效的基础URL或端点未找到"
            else:
                return False, f"API错误: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "请求超时 - 请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "连接错误 - 请检查基础URL"
        except Exception as e:
            return False, f"测试失败: {str(e)}"

    def test_api_call(self, base_url: str, auth_token: str, model: str, question: str = "1+2=？") -> tuple[bool, str, dict]:
        """Test actual API call with a specific question - Full Claude Code CLI compatibility"""
        try:
            # Use exact Claude Code CLI headers from actual implementation
            headers = {
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": auth_token,
                "user-agent": "claude-cli/1.0.115 (external, cli)",
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br"
            }

            data = {
                "model": model,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": question}]
            }

            url = f"{base_url.rstrip('/')}/v1/messages"

            # Use requests.Session for better connection handling like Claude Code
            session = requests.Session()
            session.headers.update(headers)

            # Remove debug output for normal operation
            # print(f"API Test Debug:")
            # print(f"URL: {url}")
            # print(f"Headers: {dict(session.headers)}")
            # print(f"Data: {data}")

            response = session.post(url, json=data, timeout=30)

            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text[:500]}...")  # First 500 chars

            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("content", [{}])[0].get("text", "")
                return True, "API调用成功", {
                    "question": question,
                    "answer": content,
                    "response_data": response_data,
                    "model": model,
                    "usage": response_data.get("usage", {})
                }
            else:
                try:
                    error_data = response.json()
                    error_type = error_data.get("error", {}).get("type", "unknown")
                    error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")

                    # Provide more specific error messages
                    if response.status_code == 401:
                        error_msg = f"认证失败: {error_msg}"
                    elif response.status_code == 403:
                        error_msg = f"访问被禁止: {error_msg} - 请检查API Key是否有效"
                    elif response.status_code == 404:
                        error_msg = f"端点未找到: {error_msg} - 请检查基础URL是否正确"
                    elif response.status_code == 429:
                        error_msg = f"请求频率限制: {error_msg}"
                    elif response.status_code >= 500:
                        error_msg = f"服务器错误: {error_msg}"
                    else:
                        error_msg = f"API错误 ({error_type}): {error_msg}"

                except:
                    error_msg = f"HTTP {response.status_code} - 响应格式错误"
                return False, error_msg, {}

        except requests.exceptions.Timeout:
            return False, "请求超时", {}
        except requests.exceptions.ConnectionError:
            return False, "连接错误", {}
        except Exception as e:
            return False, f"调用失败: {str(e)}", {}

    def add_config(self, name: str, base_url: str, auth_token: str, model: str) -> bool:
        """Add a new configuration"""
        # Check if name already exists
        for config in self.configs_data["configs"]:
            if config["name"] == name:
                return False

        new_config = {
            "name": name,
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": auth_token,
            "default_model": model
        }

        self.configs_data["configs"].append(new_config)
        self.save_configs_data()
        return True

    def update_config(self, old_name: str, name: str, base_url: str, auth_token: str, model: str) -> bool:
        """Update an existing configuration"""
        # Check if new name conflicts with another config
        for config in self.configs_data["configs"]:
            if config["name"] == name and config["name"] != old_name:
                return False

        for config in self.configs_data["configs"]:
            if config["name"] == old_name:
                config["name"] = name
                config["ANTHROPIC_BASE_URL"] = base_url
                config["ANTHROPIC_AUTH_TOKEN"] = auth_token
                config["default_model"] = model

                # Update active config name if it was changed
                if self.configs_data["active_config"] == old_name:
                    self.configs_data["active_config"] = name

                self.save_configs_data()
                return True
        return False

    def delete_config(self, name: str) -> bool:
        """Delete a configuration"""
        for i, config in enumerate(self.configs_data["configs"]):
            if config["name"] == name:
                del self.configs_data["configs"][i]

                # Clear active config if it was deleted
                if self.configs_data["active_config"] == name:
                    self.configs_data["active_config"] = None

                self.save_configs_data()
                return True
        return False

    def switch_to_config(self, name: str) -> bool:
        """Switch to a specific configuration"""
        for config in self.configs_data["configs"]:
            if config["name"] == name:
                try:
                    # Create settings.json content
                    settings_content = {
                        "ANTHROPIC_BASE_URL": config["ANTHROPIC_BASE_URL"],
                        "ANTHROPIC_AUTH_TOKEN": config["ANTHROPIC_AUTH_TOKEN"],
                        "default_model": config["default_model"]
                    }

                    # Write to settings.json
                    self.claude_dir.mkdir(exist_ok=True)
                    with open(self.settings_file, 'w', encoding='utf-8') as f:
                        json.dump(settings_content, f, indent=2)

                    # Update active config
                    self.configs_data["active_config"] = name
                    self.save_configs_data()

                    return True
                except Exception:
                    return False
        return False

    def open_config_manager(self):
        """Open the configuration management dialog"""
        ConfigManagerDialog(self)

    def open_api_test(self):
        """Open the API test dialog"""
        APITestDialog(self)


class APITestDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = ctk.CTkToplevel(parent.root)
        self.dialog.title("API 测试")
        self.dialog.geometry("900x700")
        self.dialog.configure(fg_color=COLORS["bg_primary"])

        # Center the dialog
        self.dialog.transient(parent.root)
        self.dialog.grab_set()
        self.dialog.focus_set()

        self.test_history = []
        self.setup_ui()
        self.load_active_config()

    def setup_ui(self):
        # Main container
        main_container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="Claude API 测试",
            font=self.parent.get_font(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(pady=(0, 20))

        # Configuration section
        config_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"])
        config_frame.pack(fill="x", pady=(0, 15))

        config_content = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_content.pack(fill="x", padx=15, pady=15)

        # Config selection
        config_label = ctk.CTkLabel(
            config_content,
            text="选择配置:",
            font=self.parent.get_font(size=12),
            text_color=COLORS["text_primary"]
        )
        config_label.pack(anchor="w")

        # Config dropdown
        self.config_var = ctk.StringVar()
        self.config_dropdown = ctk.CTkComboBox(
            config_content,
            values=self.get_config_names(),
            variable=self.config_var,
            font=self.parent.get_font(size=11),
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_primary"],
            dropdown_text_color=COLORS["text_primary"]
        )
        self.config_dropdown.pack(fill="x", pady=(5, 15))

        # Question input
        question_label = ctk.CTkLabel(
            config_content,
            text="测试问题:",
            font=self.parent.get_font(size=12),
            text_color=COLORS["text_primary"]
        )
        question_label.pack(anchor="w")

        self.question_entry = ctk.CTkEntry(
            config_content,
            placeholder_text="例如: 1+2=？ 或者 介绍一下人工智能",
            font=self.parent.get_font(size=12),
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.question_entry.pack(fill="x", pady=(5, 15))

        # Test button
        test_btn = ctk.CTkButton(
            config_content,
            text="🚀 开始测试",
            command=self.run_api_test,
            height=40,
            font=self.parent.get_font(size=12, weight="bold"),
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            text_color="white"
        )
        test_btn.pack(fill="x", pady=(5, 0))

        # Results section
        results_frame = ctk.CTkFrame(main_container, fg_color=COLORS["bg_secondary"])
        results_frame.pack(fill="both", expand=True, pady=(0, 15))

        results_header = ctk.CTkFrame(results_frame, fg_color="transparent")
        results_header.pack(fill="x", padx=15, pady=(10, 5))

        results_title = ctk.CTkLabel(
            results_header,
            text="测试结果",
            font=self.parent.get_font(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        results_title.pack(side="left")

        clear_btn = ctk.CTkButton(
            results_header,
            text="清空记录",
            command=self.clear_history,
            width=80,
            font=self.parent.get_font(size=11),
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"]
        )
        clear_btn.pack(side="right")

        # Results area
        self.results_container = ctk.CTkScrollableFrame(results_frame, fg_color=COLORS["bg_tertiary"])
        self.results_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Close button
        close_btn = ctk.CTkButton(
            main_container,
            text="关闭",
            command=self.close_dialog,
            width=100,
            font=self.parent.get_font(size=12),
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"]
        )
        close_btn.pack(pady=(10, 0))

    def get_config_names(self):
        """Get list of configuration names"""
        return [config["name"] for config in self.parent.configs_data["configs"]]

    def load_active_config(self):
        """Load active configuration if available"""
        active_config = self.parent.configs_data.get("active_config")
        if active_config:
            config_names = self.get_config_names()
            if active_config in config_names:
                self.config_var.set(active_config)
                self.question_entry.insert(0, "1+2=？")

    def run_api_test(self):
        """Run the API test"""
        config_name = self.config_var.get()
        question = self.question_entry.get().strip()

        if not config_name:
            self.show_result("错误", "请选择一个配置", None)
            return

        if not question:
            self.show_result("错误", "请输入测试问题", None)
            return

        # Find the selected configuration
        selected_config = None
        for config in self.parent.configs_data["configs"]:
            if config["name"] == config_name:
                selected_config = config
                break

        if not selected_config:
            self.show_result("错误", "配置未找到", None)
            return

        # Show loading state
        self.show_result("测试中", f"正在测试配置: {config_name}\\n问题: {question}\\n请稍等...", None)

        # Run test in background thread
        import threading

        def run_test():
            success, message, result_data = self.parent.test_api_call(
                selected_config["ANTHROPIC_BASE_URL"],
                selected_config["ANTHROPIC_AUTH_TOKEN"],
                selected_config["default_model"],  # Use model from selected config
                question
            )

            # Update UI in main thread
            self.dialog.after(0, lambda: self.test_complete(success, message, result_data, selected_config))

        threading.Thread(target=run_test, daemon=True).start()

    def test_complete(self, success, message, result_data, config):
        """Handle test completion"""
        if success:
            answer = result_data.get("answer", "无回复")
            usage = result_data.get("usage", {})
            model = result_data.get("model", "未知")

            result_text = f"✅ {message}\\n\\n"
            result_text += f"📋 问题: {result_data.get('question', '')}\\n\\n"
            result_text += f"🤖 回答:\\n{answer}\\n\\n"
            result_text += f"📊 使用信息:\\n"
            result_text += f"   模型: {model}\\n"
            if usage:
                result_text += f"   输入token: {usage.get('input_tokens', 0)}\\n"
                result_text += f"   输出token: {usage.get('output_tokens', 0)}\\n"
                result_text += f"   总token: {usage.get('total_tokens', 0)}"

            self.show_result("✅ 测试成功", result_text, result_data)
        else:
            error_text = f"❌ {message}\\n\\n"
            error_text += f"🔧 配置: {config['name']}\\n"
            error_text += f"🌐 URL: {config['ANTHROPIC_BASE_URL']}\\n"
            error_text += f"🤖 模型: {config['default_model']}"

            self.show_result("❌ 测试失败", error_text, None)

    def show_result(self, title, content, data):
        """Show test result in the results area"""
        result_frame = ctk.CTkFrame(self.results_container, fg_color=COLORS["bg_primary"])
        result_frame.pack(fill="x", pady=5, padx=10)

        # Title
        title_label = ctk.CTkLabel(
            result_frame,
            text=title,
            font=self.parent.get_font(size=12, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        title_label.pack(fill="x", padx=10, pady=(10, 5))

        # Content
        content_textbox = ctk.CTkTextbox(
            result_frame,
            height=150,
            font=self.parent.get_font(size=11),
            fg_color=COLORS["bg_secondary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            wrap="word"
        )
        content_textbox.pack(fill="x", padx=10, pady=(0, 10))
        content_textbox.insert("1.0", content)
        content_textbox.configure(state="disabled")

        # Store for clearing
        result_frame._title_label = title_label
        result_frame._content_textbox = content_textbox

    def clear_history(self):
        """Clear test history"""
        for widget in self.results_container.winfo_children():
            widget.destroy()

    def close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()


class ConfigManagerDialog:
    def __init__(self, parent):
        self.parent = parent
        self.dialog = ctk.CTkToplevel(parent.root)
        self.dialog.title("配置管理器")
        self.dialog.geometry("800x600")
        self.dialog.configure(fg_color=COLORS["bg_primary"])

        # Center the dialog
        self.dialog.transient(parent.root)
        self.dialog.grab_set()

        # Make dialog modal
        self.dialog.focus_set()

        self.selected_config = None
        self.setup_ui()
        self.refresh_config_list()

    def get_font(self, size=12, weight="normal"):
        """Get a font with Chinese support"""
        return self.parent.get_font(size, weight)

    def setup_ui(self):
        # Main container
        main_container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="配置管理器",
            font=self.get_font(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(pady=(0, 20))

        # Content area
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Left panel - Config list
        left_panel = ctk.CTkFrame(content_frame, width=300, fg_color=COLORS["bg_secondary"])
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Config list header
        list_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        list_header.pack(fill="x", padx=10, pady=10)

        list_title = ctk.CTkLabel(
            list_header,
            text="配置列表",
            font=self.get_font(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        list_title.pack(side="left")

        # Add and Batch Test buttons
        buttons_frame = ctk.CTkFrame(list_header, fg_color="transparent")
        buttons_frame.pack(side="right")

        self.batch_test_btn = ctk.CTkButton(
            buttons_frame,
            text="批量测试",
            command=self.batch_test_configs,
            width=75,
            height=25,
            font=self.get_font(size=11),
            fg_color=COLORS["warning_orange"],
            hover_color="#e68900"
        )
        self.batch_test_btn.pack(side="right", padx=(0, 5))

        self.add_btn = ctk.CTkButton(
            buttons_frame,
            text="+ 添加",
            command=self.add_config,
            width=60,
            height=25,
            font=self.get_font(size=12),
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"]
        )
        self.add_btn.pack(side="right")

        # Config list
        list_frame = ctk.CTkFrame(left_panel, fg_color=COLORS["bg_tertiary"])
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.config_list = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.config_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Right panel - Config details and actions
        right_panel = ctk.CTkFrame(content_frame, fg_color=COLORS["bg_secondary"])
        right_panel.pack(side="right", fill="both", expand=True)

        # Right panel content
        right_content = ctk.CTkFrame(right_panel, fg_color="transparent")
        right_content.pack(fill="both", expand=True, padx=15, pady=15)

        # Config details title
        details_title = ctk.CTkLabel(
            right_content,
            text="配置详情",
            font=self.get_font(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        details_title.pack(anchor="w", pady=(0, 15))

        # Config details form
        self.details_frame = ctk.CTkFrame(right_content, fg_color=COLORS["bg_tertiary"])
        self.details_frame.pack(fill="both", expand=True)

        self.setup_details_form()

        # Bottom buttons
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            command=self.close_dialog,
            width=80,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=self.get_font(size=12)
        )
        close_btn.pack(side="right")

    def setup_details_form(self):
        form_content = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        form_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Name field
        name_frame = ctk.CTkFrame(form_content, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 15))

        name_label = ctk.CTkLabel(
            name_frame,
            text="配置名称:",
            font=self.get_font(size=12),
            text_color=COLORS["text_primary"]
        )
        name_label.pack(anchor="w")

        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="请输入配置名称",
            font=self.get_font(size=12),
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.name_entry.pack(fill="x", pady=(5, 0))

        # Base URL field
        url_frame = ctk.CTkFrame(form_content, fg_color="transparent")
        url_frame.pack(fill="x", pady=(0, 15))

        url_label = ctk.CTkLabel(
            url_frame,
            text="ANTHROPIC_BASE_URL:",
            font=self.get_font(size=12),
            text_color=COLORS["text_primary"]
        )
        url_label.pack(anchor="w")

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://api.anthropic.com",
            font=self.get_font(size=12),
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.url_entry.pack(fill="x", pady=(5, 0))

        # Auth token field
        token_frame = ctk.CTkFrame(form_content, fg_color="transparent")
        token_frame.pack(fill="x", pady=(0, 15))

        token_label = ctk.CTkLabel(
            token_frame,
            text="ANTHROPIC_AUTH_TOKEN:",
            font=self.get_font(size=12),
            text_color=COLORS["text_primary"]
        )
        token_label.pack(anchor="w")

        self.token_entry = ctk.CTkEntry(
            token_frame,
            placeholder_text="sk-ant-api03-...",
            show="*",
            font=self.get_font(size=12),
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"]
        )
        self.token_entry.pack(fill="x", pady=(5, 0))

        # Model field
        model_frame = ctk.CTkFrame(form_content, fg_color="transparent")
        model_frame.pack(fill="x", pady=(0, 20))

        model_label = ctk.CTkLabel(
            model_frame,
            text="默认模型:",
            font=self.get_font(size=12),
            text_color=COLORS["text_primary"]
        )
        model_label.pack(anchor="w")

        self.model_var = ctk.StringVar(value="claude-sonnet-4-20250514")
        self.model_dropdown = ctk.CTkComboBox(
            model_frame,
            values=self.parent.get_available_models(),
            variable=self.model_var,
            font=self.get_font(size=12),
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_primary"],
            dropdown_text_color=COLORS["text_primary"]
        )
        self.model_dropdown.pack(fill="x", pady=(5, 0))

        # Action buttons
        button_frame = ctk.CTkFrame(form_content, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        # Test button
        self.test_btn = ctk.CTkButton(
            button_frame,
            text="测试配置",
            command=self.test_current_config,
            width=100,
            fg_color=COLORS["warning_orange"],
            hover_color="#e68900",
            text_color="white",
            font=self.get_font(size=12)
        )
        self.test_btn.pack(side="left", padx=(0, 10))

        # Save button
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="保存",
            command=self.save_config,
            width=80,
            fg_color=COLORS["success_green"],
            hover_color="#45a049",
            text_color="white",
            font=self.get_font(size=12)
        )
        self.save_btn.pack(side="left", padx=(0, 10))

        # Delete button
        self.delete_btn = ctk.CTkButton(
            button_frame,
            text="删除",
            command=self.delete_config,
            width=80,
            fg_color=COLORS["accent_red"],
            hover_color=COLORS["accent_red_hover"],
            text_color="white",
            font=self.get_font(size=12)
        )
        self.delete_btn.pack(side="left", padx=(0, 10))

        # Switch button
        self.switch_btn = ctk.CTkButton(
            button_frame,
            text="切换至",
            command=self.switch_to_config,
            width=80,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=self.get_font(size=12)
        )

        # API Test button
        self.api_test_btn = ctk.CTkButton(
            button_frame,
            text="API测试",
            command=self.open_api_test,
            width=80,
            fg_color=COLORS["warning_orange"],
            hover_color="#e68900",
            text_color="white",
            font=self.get_font(size=12)
        )
        self.api_test_btn.pack(side="right", padx=(10, 0))
        self.switch_btn.pack(side="right")

        # Status label
        self.status_label = ctk.CTkLabel(
            form_content,
            text="",
            font=self.get_font(size=11),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(pady=(10, 0))

        self.clear_form()

    def open_api_test(self):
        """Open API test dialog from config manager"""
        APITestDialog(self.parent)

    def refresh_config_list(self):
        self.refresh_config_list_with_selection(None)

    def refresh_config_list_with_selection(self, selected_name):
        # Clear existing items
        for widget in self.config_list.winfo_children():
            widget.destroy()

        # Add config items
        for config in self.parent.configs_data["configs"]:
            self.create_config_item(config)

        # Restore selection if specified
        if selected_name:
            for widget in self.config_list.winfo_children():
                if hasattr(widget, '_config_data') and widget._config_data["name"] == selected_name:
                    self.select_config(widget._config_data)
                    break

    def create_config_item(self, config):
        # Simple item with just name and minimal status
        item_frame = ctk.CTkFrame(self.config_list, fg_color=COLORS["bg_primary"])
        item_frame.pack(fill="x", pady=1, padx=2)

        # Main content frame - compact layout
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=8, pady=6)

        # Name label
        name_label = ctk.CTkLabel(
            content_frame,
            text=config["name"],
            font=self.get_font(size=12),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        name_label.pack(side="left")

        # Status indicators on the right - compact
        status_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        status_container.pack(side="right")

        # Test status (simple colored circle)
        test_status = config.get('test_status', None)
        if test_status == 'success':
            status_circle = ctk.CTkLabel(
                status_container,
                text="●",
                font=self.get_font(size=14),
                text_color=COLORS["success_green"]
            )
            status_circle.pack(side="right", padx=(0, 3))
        elif test_status == 'failed':
            status_circle = ctk.CTkLabel(
                status_container,
                text="●",
                font=self.get_font(size=14),
                text_color=COLORS["accent_red"]
            )
            status_circle.pack(side="right", padx=(0, 3))
        elif test_status == 'testing':
            status_circle = ctk.CTkLabel(
                status_container,
                text="●",
                font=self.get_font(size=14),
                text_color=COLORS["warning_orange"]
            )
            status_circle.pack(side="right", padx=(0, 3))

        # Active indicator (small text)
        if config["name"] == self.parent.configs_data.get("active_config"):
            active_text = ctk.CTkLabel(
                status_container,
                text="活跃",
                font=self.get_font(size=9),
                text_color=COLORS["success_green"],
                fg_color=COLORS["bg_primary"]
            )
            active_text.pack(side="right", padx=(0, 5))

        # Click binding
        def on_click(event, cfg=config):
            self.select_config(cfg)

        # Bind click to all widgets
        for widget in [item_frame, content_frame, name_label]:
            widget.bind("<Button-1>", on_click)
            if status_container in locals():
                status_container.bind("<Button-1>", on_click)

        # Store reference for selection highlighting
        item_frame._config_data = config
        item_frame._is_selected = False

    def select_config(self, config):
        self.selected_config = config

        # Update form with config data
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, config["name"])

        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, config["ANTHROPIC_BASE_URL"])

        self.token_entry.delete(0, "end")
        self.token_entry.insert(0, config["ANTHROPIC_AUTH_TOKEN"])

        self.model_var.set(config["default_model"])

        # Update form state
        self.save_btn.configure(text="更新")
        self.delete_btn.configure(state="normal")
        self.switch_btn.configure(state="normal")

        # Update visual selection
        for widget in self.config_list.winfo_children():
            if hasattr(widget, '_config_data'):
                if widget._config_data["name"] == config["name"]:
                    widget.configure(fg_color=COLORS["accent_primary"])
                    widget._is_selected = True
                else:
                    widget.configure(fg_color=COLORS["bg_primary"])
                    widget._is_selected = False

    def clear_form(self):
        self.selected_config = None
        self.name_entry.delete(0, "end")
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, "https://api.anthropic.com")
        self.token_entry.delete(0, "end")
        self.model_var.set("claude-sonnet-4-20250514")

        self.save_btn.configure(text="保存")
        self.delete_btn.configure(state="disabled")
        self.switch_btn.configure(state="disabled")

        # Clear selection highlighting
        for widget in self.config_list.winfo_children():
            if hasattr(widget, '_config_data'):
                widget.configure(fg_color=COLORS["bg_primary"])

    def add_config(self):
        self.clear_form()
        self.name_entry.focus()

    def save_config(self):
        name = self.name_entry.get().strip()
        base_url = self.url_entry.get().strip()
        auth_token = self.token_entry.get().strip()
        model = self.model_var.get()

        if not all([name, base_url, auth_token, model]):
            self.show_status("请填写所有字段", COLORS["accent_red"])
            return

        if self.selected_config:
            # Update existing config
            old_name = self.selected_config["name"]
            if self.parent.update_config(old_name, name, base_url, auth_token, model):
                self.show_status("配置更新成功", COLORS["success_green"])
                self.refresh_config_list()
                # Select the updated config
                for config in self.parent.configs_data["configs"]:
                    if config["name"] == name:
                        self.select_config(config)
                        break
            else:
                self.show_status("更新失败：名称已存在", COLORS["accent_red"])
        else:
            # Add new config
            if self.parent.add_config(name, base_url, auth_token, model):
                self.show_status("配置添加成功", COLORS["success_green"])
                self.refresh_config_list()
                # Select the new config
                for config in self.parent.configs_data["configs"]:
                    if config["name"] == name:
                        self.select_config(config)
                        break
            else:
                self.show_status("添加失败：名称已存在", COLORS["accent_red"])

    def delete_config(self):
        if not self.selected_config:
            return

        name = self.selected_config["name"]
        result = messagebox.askyesno(
            "确认删除",
            f"您确定要删除配置 '{name}' 吗？",
            parent=self.dialog
        )

        if result:
            if self.parent.delete_config(name):
                self.show_status("配置删除成功", COLORS["success_green"])
                self.refresh_config_list()
                self.clear_form()
            else:
                self.show_status("删除配置失败", COLORS["accent_red"])

    def switch_to_config(self):
        if not self.selected_config:
            return

        name = self.selected_config["name"]
        if self.parent.switch_to_config(name):
            self.show_status(f"已切换到配置 '{name}'", COLORS["success_green"])
            self.refresh_config_list()
            # Refresh the main window
            self.parent.refresh_config_list()
        else:
            self.show_status("切换配置失败", COLORS["accent_red"])

    def test_current_config(self):
        base_url = self.url_entry.get().strip()
        auth_token = self.token_entry.get().strip()
        model = self.model_var.get()

        if not all([base_url, auth_token, model]):
            self.show_status("请在测试前填写所有字段", COLORS["accent_red"])
            return

        self.test_btn.configure(text="测试中...", state="disabled")
        self.dialog.update()

        # Run test in a separate thread to avoid blocking UI
        import threading

        def run_test():
            success, message = self.parent.test_config(base_url, auth_token, model)

            # Update UI in main thread
            self.dialog.after(0, lambda: self.test_complete(success, message))

        threading.Thread(target=run_test, daemon=True).start()

    def test_complete(self, success, message):
        self.test_btn.configure(text="测试配置", state="normal")
        color = COLORS["success_green"] if success else COLORS["accent_red"]
        self.show_status(f"测试结果: {message}", color, permanent=True)  # 永久显示测试结果

    def show_status(self, message, color, permanent=False):
        self.status_label.configure(text=message, text_color=color)
        # Only clear after 5 seconds if not permanent
        if not permanent:
            self.dialog.after(5000, lambda: self.status_label.configure(text=""))

    def close_dialog(self):
        self.dialog.destroy()

    def batch_test_configs(self):
        """批量测试所有配置"""
        configs = self.parent.configs_data["configs"]
        if not configs:
            self.show_status("没有配置可供测试", COLORS["accent_red"])
            return

        self.batch_test_btn.configure(text="测试中...", state="disabled")
        self.show_status("开始批量测试...", COLORS["text_muted"])

        # Reset all test statuses
        for config in configs:
            config['test_status'] = 'testing'

        self.refresh_config_list()

        # Run batch test in background
        import threading

        def run_batch_test():
            # Store current selection
            selected_name = self.selected_config["name"] if self.selected_config else None

            for i, config in enumerate(configs):
                try:
                    success, message = self.parent.test_config(
                        config["ANTHROPIC_BASE_URL"],
                        config["ANTHROPIC_AUTH_TOKEN"],
                        config["default_model"]
                    )
                    config['test_status'] = 'success' if success else 'failed'
                    config['test_message'] = message
                except Exception as e:
                    config['test_status'] = 'failed'
                    config['test_message'] = str(e)

                # Update UI in main thread after each test
                self.dialog.after(0, lambda: self.refresh_config_list_with_selection(selected_name))

            # All tests completed
            self.dialog.after(0, lambda: self.batch_test_complete())

        threading.Thread(target=run_batch_test, daemon=True).start()

    def batch_test_complete(self):
        """批量测试完成"""
        self.batch_test_btn.configure(text="批量测试", state="normal")
        configs = self.parent.configs_data["configs"]

        success_count = sum(1 for c in configs if c.get('test_status') == 'success')
        total_count = len(configs)

        if success_count == total_count:
            self.show_status(f"批量测试完成：全部 {total_count} 个配置测试通过", COLORS["success_green"], permanent=True)
        else:
            self.show_status(f"批量测试完成：{success_count}/{total_count} 个配置测试通过", COLORS["accent_red"], permanent=True)


def main():
    app = ClaudeConfigSwitcher()
    app.run()


if __name__ == "__main__":
    main()
