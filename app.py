import os
import json
import time
import threading
import requests
import platform
from tkinter import *
from tkinter import filedialog, messagebox
import customtkinter as tk
from PIL import Image, ImageTk, ImageOps
import fakeredis
import mysql.connector
import shutil
import zipfile


from background_manager import BackgroundManager

APP_DIR = os.path.dirname(os.path.abspath(__file__))

local_redis = fakeredis.FakeStrictRedis(decode_responses=True)

CENTRAL_SERVER_URL = "http://127.0.0.1:8000/api/vote"

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root_1234",
    "database": "local_backup_election"
}

tk.set_appearance_mode("dark")
mode = "dark"
root = tk.CTk()
root.title("Node - Election App")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")

DATA_FILE = "election_data.json"
IMAGE_DIR = "candidate_images"

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def sync_worker():
    while True:
        try:
            queue_length = local_redis.llen("local_vote_queue")
            if queue_length > 0:
                vote_json = local_redis.lindex("local_vote_queue", 0)
                vote_data = json.loads(vote_json)

                response = requests.post(CENTRAL_SERVER_URL, json=vote_data, timeout=5)

                if response.status_code == 200:
                    local_redis.lpop("local_vote_queue")
        except Exception as e:
            time.sleep(5)
        time.sleep(1) #

threading.Thread(target=sync_worker, daemon=True).start()

def init_local_mysql():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {MYSQL_CONFIG['database']}")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_ledger (
                vote_id VARCHAR(50) PRIMARY KEY,
                candidate_name VARCHAR(100),
                position VARCHAR(50),
                candidate_class VARCHAR(50),
                candidate_section VARCHAR(50),
                timestamp DATETIME
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("[Database] Local MySQL backup ledger verified.")
    except Exception as e:
        print(f"[Database Error] Local MySQL offline (Using Redis Cache only): {e}")

init_local_mysql()

candidate_rows = []
available_positions = []
ballot_frame = None
current_post_index = 0
positions_container = None

def load_data():
    default_data = {
        "password": "1234",
        "background_path_light": "default_light_bg.jpg",
        "background_path_dark": "default_dark_bg.jpg",
        "positions": ["SPL", "ASPL"],
        "candidates": [],
        "image_size": 140,
        "image_spacing": 20,
        "font_family": "Arial",
        "text_size": 16,
        "aspect_ratio_fix": False,
        "show_voting_popup": True,
        "play_voting_sound": True,
        "show_popup_images": True,
        "show_image_borders": True,
        "font_color": "#FFFFFF"
    }
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            for key, val in default_data.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

app_data = load_data()
available_positions = app_data.get("positions", ["SPL", "ASPL"])

bg_manager = BackgroundManager(
    root,
    app_data,
    get_ballot_frame=lambda: ballot_frame,
    base_dir=APP_DIR,
)


class ImageEditor(tk.CTkToplevel):
    def __init__(self, parent, image_path, callback):
        super().__init__(parent)
        self.title("Candidate Photo Editor")
        self.geometry("700x800")
        self.attributes("-topmost", True)
        self.resizable(False, False)

        self.callback = callback
        self.original_pil = Image.open(image_path)
        self.original_pil = ImageOps.exif_transpose(self.original_pil)
        self.current_pil = self.original_pil.copy()

        self.setup_ui()

        self.rect = None
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        self.after(200, self.refresh_canvas)

    def setup_ui(self):
        tk.CTkLabel(self, text="IMAGE EDITOR", font=("Arial", 18, "bold")).pack(pady=10)
        tk.CTkLabel(self, text="How to crop: Click and Drag your mouse over the face area", text_color="#3b7bb2").pack()

        self.canvas_frame = tk.CTkFrame(self, fg_color="#111111", width=600, height=500)
        self.canvas_frame.pack(pady=10, padx=20)
        self.canvas_frame.pack_propagate(False)

        self.canvas = Canvas(self.canvas_frame, bg="#111111", highlightthickness=0, cursor="cross")
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        self.canvas.bind("<ButtonPress-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

        ctrl_frame = tk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=50, pady=10)

        tk.CTkButton(ctrl_frame, text="⟲ Rotate Left", width=120, command=lambda: self.rotate_img(-90)).pack(
            side="left", padx=10)
        tk.CTkButton(ctrl_frame, text="Rotate Right ⟳", width=120, command=lambda: self.rotate_img(90)).pack(
            side="right", padx=10)

        footer = tk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=20, padx=50)

        tk.CTkButton(footer, text="Cancel", fg_color="#a83232", hover_color="#7a2222", command=self.destroy).pack(
            side="left")
        tk.CTkButton(footer, text="Apply Crop & Save", fg_color="#1e5228", hover_color="#14361b",
                     command=self.save_result).pack(side="right")

    def refresh_canvas(self):
        ratio = min(600 / self.current_pil.width, 500 / self.current_pil.height)
        new_w = int(self.current_pil.width * ratio)
        new_h = int(self.current_pil.height * ratio)

        self.display_pil = self.current_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(self.display_pil)

        self.canvas.config(width=new_w, height=new_h)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        self.canvas.image = self.tk_img
        self.img_scale_ratio = ratio

    def rotate_img(self, angle):
        self.current_pil = self.current_pil.rotate(angle, expand=True)
        self.refresh_canvas()

    def start_crop(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                 outline="white", width=2, dash=(4, 4))

    def draw_crop(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)

    def end_crop(self, event):
        self.end_x = event.x
        self.end_y = event.y

    def save_result(self):
        if self.rect and abs(self.start_x - self.end_x) > 5:
            left = min(self.start_x, self.end_x) / self.img_scale_ratio
            top = min(self.start_y, self.end_y) / self.img_scale_ratio
            right = max(self.start_x, self.end_x) / self.img_scale_ratio
            bottom = max(self.start_y, self.end_y) / self.img_scale_ratio

            self.current_pil = self.current_pil.crop((left, top, right, bottom))

        final_filename = f"edited_{int(time.time())}.png"
        final_path = os.path.abspath(os.path.join(IMAGE_DIR, final_filename))

        self.current_pil.save(final_path, "PNG")

        self.callback(final_path)
        self.destroy()

def show_vote_notification(candidate_name):
    toast = tk.CTkFrame(root, corner_radius=10, fg_color="#1e5228", border_width=2, border_color="#50C878")
    toast.place(relx=0.98, rely=0.05, anchor="ne")

    label = tk.CTkLabel(toast, text=f"Voted for: {candidate_name}", font=("Arial", 14, "bold"), text_color="white", padx=20, pady=10)
    label.pack()

    try:
        root.bell()
    except:
        pass

    root.after(2000, toast.destroy)

def start_voting_session():
    global current_post_index, ballot_frame

    next_vote_btn.configure(border_width=2, fg_color="#1a1a1a", border_color="#111111")
    root.update()
    time.sleep(0.1)

    bg_manager.refresh_voting()
    root.update_idletasks()
    if bg_manager.bg_label:
        bg_manager.bg_label.lower()

    current_post_index = 0
    next_vote_btn.place_forget()

    ballot_frame = tk.CTkFrame(root, fg_color="transparent")
    ballot_frame.place(relx=0.5, rely=0.5, anchor="center")

    render_current_ballot_post()

def render_current_ballot_post():
    global ballot_frame, current_post_index

    for widget in ballot_frame.winfo_children():
        widget.destroy()

    if current_post_index >= len(available_positions):
        ballot_frame.destroy()
        bg_manager.refresh_welcome()
        next_vote_btn.place(relx=0.49, rely=0.70, anchor="nw")
        return

    target_post = available_positions[current_post_index]

    selected_font = app_data.get("font_family", "Arial")
    selected_size = app_data.get("text_size", 16)
    selected_color = app_data.get("font_color", "#FFFFFF")
    custom_spacing = app_data.get("image_spacing", 20)
    custom_img_size = app_data.get("image_size", 140)
    border_thickness = 2 if app_data.get("show_image_borders", True) else 0

    header = tk.CTkLabel(
        ballot_frame,
        text=f"VOTE FOR YOUR: {target_post.upper()}",
        font=(selected_font, int(selected_size * 1.5), "bold"),
        text_color=selected_color
    )
    header.pack(pady=30)

    cards_container = tk.CTkFrame(ballot_frame, fg_color="transparent")
    cards_container.pack()

    matching_candidates = [c for c in app_data.get("candidates", []) if c.get("position") == target_post]

    if not matching_candidates:
        current_post_index += 1
        render_current_ballot_post()
        return

    for cand in matching_candidates:
        card_width = custom_img_size + 80
        card_height = custom_img_size + 200

        card = tk.CTkFrame(
            cards_container,
            width=card_width,
            height=card_height,
            border_width=border_thickness,
            border_color="#3a3a3a"
        )
        card.pack(side="left", padx=custom_spacing, pady=10)
        card.pack_propagate(False)

        img_path = cand.get("image_path", "")
        if img_path and os.path.exists(img_path):
            try:
                p_img = Image.open(img_path)
                if app_data.get("aspect_ratio_fix", False):
                    calculated_w = int(custom_img_size * 0.85)
                    p_img = p_img.resize((calculated_w, custom_img_size), Image.Resampling.LANCZOS)
                    ctk_img = tk.CTkImage(light_image=p_img, dark_image=p_img, size=(calculated_w, custom_img_size))
                else:
                    p_img = p_img.resize((custom_img_size, custom_img_size), Image.Resampling.LANCZOS)
                    ctk_img = tk.CTkImage(light_image=p_img, dark_image=p_img, size=(custom_img_size, custom_img_size))
                img_label = tk.CTkLabel(card, text="", image=ctk_img)
            except Exception:
                img_label = tk.CTkLabel(card, text="[ Image Error ]", width=custom_img_size, height=custom_img_size, fg_color="#2b2b2b")
        else:
            img_label = tk.CTkLabel(card, text="[ No Image ]", width=custom_img_size, height=custom_img_size, fg_color="#2b2b2b")
        img_label.pack(pady=15)

        name_label = tk.CTkLabel(
            card,
            text=cand.get("name", "Unknown"),
            font=(selected_font, selected_size, "bold"),
            text_color=selected_color,
            wraplength=card_width - 20
        )
        name_label.pack(pady=2)

        class_text = f"Class: {cand.get('candidate_class', '')} - {cand.get('candidate_section', '').upper()}"
        metadata_label = tk.CTkLabel(
            card,
            text=class_text,
            font=(selected_font, int(selected_size * 0.8)),
            text_color="#888888"
        )
        metadata_label.pack(pady=2)

        indicator_dot = tk.CTkLabel(card, text="", width=18, height=18, fg_color="#4a1515", corner_radius=9)
        indicator_dot.pack(pady=5)

        vote_btn = tk.CTkButton(
            card,
            text="VOTE",
            font=(selected_font, int(selected_size * 0.9), "bold"),
            fg_color="#1e5228",
            hover_color="#153b1d",
            command=lambda c=cand, dot=indicator_dot: record_vote_action(c, dot)
        )
        vote_btn.pack(pady=15, side="bottom")

def record_vote_action(candidate_data, target_dot):
    target_dot.configure(fg_color="#FF0000")
    show_vote_notification(candidate_data["name"])
    vote_id = f"VOTE_{time.time_ns()}"
    timestamp_formatted = time.strftime('%Y-%m-%d %H:%M:%S')

    vote_payload = {
        "vote_id": vote_id,
        "candidate_name": candidate_data["name"],
        "position": candidate_data["position"],
        "candidate_class": candidate_data.get("candidate_class", ""),
        "candidate_section": candidate_data.get("candidate_section", ""),
        "timestamp": timestamp_formatted
    }

    local_redis.rpush("local_vote_queue", json.dumps(vote_payload))

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        query = """
            INSERT INTO local_ledger 
            (vote_id, candidate_name, position, candidate_class, candidate_section, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            vote_id,
            vote_payload["candidate_name"],
            vote_payload["position"],
            vote_payload["candidate_class"],
            vote_payload["candidate_section"],
            timestamp_formatted
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"School MySQL Server log error: {e}")

    root.after(200, progress_to_next_ballot_stage)

def progress_to_next_ballot_stage():
    global current_post_index
    current_post_index += 1
    render_current_ballot_post()

def settings():
    settings_tab = tk.CTkToplevel(root)
    settings_tab.title("Settings")
    screen_h = root.winfo_screenheight()
    win_h = min(750, screen_h - 100)
    settings_tab.geometry(f"550x{win_h}")
    settings_tab.resizable(False, False)
    settings_tab.attributes("-topmost", True)

    scroll_container = tk.CTkScrollableFrame(settings_tab, width=520, height=730)
    scroll_container.pack(fill="both", expand=True, padx=10, pady=10)

    tk.CTkLabel(scroll_container, text="Adjust Preferences", font=("Arial", 18, "bold")).pack(pady=10)
    tk.CTkLabel(scroll_container, text="Theme(Dark/Light)", font=("Arial", 12, "bold"), text_color="#3b7bb2").pack(anchor="w", pady=(10, 5))
    theme_frame = tk.CTkFrame(scroll_container)
    theme_frame.pack(fill="x", pady=5)

    def dark_light_mode_switcher():
        global mode
        if mode == "dark":
            tk.set_appearance_mode("light")
            mode = "light"
        else:
            tk.set_appearance_mode("dark")
            mode = "dark"
        bg_manager.refresh_auto()

    switch_var = tk.StringVar(value=mode)
    dark_light_mode_switch = tk.CTkSwitch(
        theme_frame,
        text="Light Mode / Dark Mode",
        command=dark_light_mode_switcher,
        variable=switch_var,
        onvalue="dark",
        offvalue="light"
    )
    dark_light_mode_switch.pack(anchor="w", padx=15, pady=10)

    def browse_light_bg():
        file_path = filedialog.askopenfilename(title="Select Light Mode Background", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            app_data["background_path_light"] = file_path
            save_data(app_data)
            bg_manager.refresh_auto()
            messagebox.showinfo("Success", "Light Mode background saved.", parent=settings_tab)

    tk.CTkButton(theme_frame, text="🖼️ Choose Light Mode Background", fg_color="#e0e0e0", text_color="#000000", hover_color="#c0c0c0", command=browse_light_bg).pack(fill="x", padx=15, pady=5)

    def browse_dark_bg():
        file_path = filedialog.askopenfilename(title="Select Dark Mode Background", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            app_data["background_path_dark"] = file_path
            save_data(app_data)
            bg_manager.refresh_auto()
            messagebox.showinfo("Success", "Dark Mode background saved.", parent=settings_tab)

    tk.CTkButton(theme_frame, text="🖼️ Choose Dark Mode Background", fg_color="#2b2b2b", text_color="#ffffff", hover_color="#1f1f1f", command=browse_dark_bg).pack(fill="x", padx=15, pady=5)

    def reset_to_basic_format():
        app_data["background_path_light"] = "default_light_bg.png"
        app_data["background_path_dark"] = "default_dark_bg.png"
        save_data(app_data)
        bg_manager.refresh_auto()
        messagebox.showinfo("Success", "Themes restored back to default system layouts!", parent=settings_tab)

    tk.CTkButton(theme_frame, text="Reset to Default Theme (Remove Images)", fg_color="#a83232", hover_color="#7a2222", command=reset_to_basic_format).pack(fill="x", padx=15, pady=10)

    tk.CTkLabel(scroll_container, text="Toggles", font=("Arial", 12, "bold"), text_color="#3b7bb2").pack(anchor="w", pady=(15, 5))
    switch_frame = tk.CTkFrame(scroll_container)
    switch_frame.pack(fill="x", pady=5)

    aspect_var = tk.BooleanVar(value=app_data.get("aspect_ratio_fix", False))
    tk.CTkSwitch(switch_frame, text="Aspect Ratio Adjustment (Fix Squished Images)", variable=aspect_var).pack(anchor="w", padx=15, pady=6)

    popup_var = tk.BooleanVar(value=app_data.get("show_voting_popup", True))
    tk.CTkSwitch(switch_frame, text="Voting Pop-up", variable=popup_var).pack(anchor="w", padx=15, pady=6)

    pop_img_var = tk.BooleanVar(value=app_data.get("show_popup_images", True))
    tk.CTkSwitch(switch_frame, text="Pop-up Images", variable=pop_img_var).pack(anchor="w", padx=15, pady=6)

    border_var = tk.BooleanVar(value=app_data.get("show_image_borders", True))
    tk.CTkSwitch(switch_frame, text="Image Borders", variable=border_var).pack(anchor="w", padx=15, pady=6)

    tk.CTkLabel(scroll_container, text="Layout, Sizing & Typography", font=("Arial", 12, "bold"), text_color="#3b7bb2").pack(anchor="w", pady=(15, 5))
    dim_frame = tk.CTkFrame(scroll_container)
    dim_frame.pack(fill="x", pady=5)

    tk.CTkLabel(dim_frame, text="Image Size:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    img_size_entry = tk.CTkEntry(dim_frame, width=80)
    img_size_entry.insert(0, str(app_data.get("image_size", 140)))
    img_size_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.CTkLabel(dim_frame, text="Space Between Images:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    spacing_entry = tk.CTkEntry(dim_frame, width=80)
    spacing_entry.insert(0, str(app_data.get("image_spacing", 20)))
    spacing_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.CTkLabel(dim_frame, text="Font Family:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    font_options = ["Arial", "Helvetica", "Times New Roman", "Courier", "Impact"]
    font_dropdown = tk.CTkOptionMenu(dim_frame, values=font_options, width=120)
    font_dropdown.set(app_data.get("font_family", "Arial"))
    font_dropdown.grid(row=2, column=1, padx=10, pady=5)

    tk.CTkLabel(dim_frame, text="Text Display Size:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
    text_size_entry = tk.CTkEntry(dim_frame, width=80)
    text_size_entry.insert(0, str(app_data.get("text_size", 16)))
    text_size_entry.grid(row=3, column=1, padx=10, pady=5)

    tk.CTkLabel(dim_frame, text="Font Colour:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
    color_map = {"White": "#FFFFFF", "Black": "#000000", "Gold": "#FFD700", "Red": "#DC143C", "Blue": "#4169E1", "Green": "#50C878"}
    color_dropdown = tk.CTkOptionMenu(dim_frame, values=list(color_map.keys()), width=120)
    current_hex = app_data.get("font_color", "#FFFFFF")
    current_name = "White"
    for name, hex_code in color_map.items():
        if hex_code == current_hex: current_name = name; break
    color_dropdown.set(current_name)
    color_dropdown.grid(row=4, column=1, padx=10, pady=5)

    def trigger_auto_config():
        screen_w = root.winfo_screenwidth()
        img_size_entry.delete(0, END)
        img_size_entry.insert(0, str(int(screen_w * 0.08)))
        messagebox.showinfo("Auto-Configuration", f"Optimized for screen width: {screen_w}px.", parent=settings_tab)

    tk.CTkButton(scroll_container, text="Auto-Configuration", fg_color="#2b5982", command=trigger_auto_config).pack(fill="x", pady=(15, 5))

    def save_settings_action():
        try:
            app_data["image_size"] = int(img_size_entry.get())
            app_data["image_spacing"] = int(spacing_entry.get())
            app_data["font_family"] = font_dropdown.get()
            app_data["text_size"] = int(text_size_entry.get())
            app_data["font_color"] = color_map.get(color_dropdown.get(), "#FFFFFF")
            app_data["aspect_ratio_fix"] = aspect_var.get()
            app_data["show_voting_popup"] = popup_var.get()
            app_data["show_popup_images"] = pop_img_var.get()
            app_data["show_image_borders"] = border_var.get()
            save_data(app_data)
            bg_manager.refresh_auto()
            messagebox.showinfo("Saved", "Preferences written successfully.", parent=settings_tab)
            settings_tab.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please verify sizes and spacing fields are numbers.", parent=settings_tab)

    tk.CTkButton(scroll_container, text="Save Changes", font=("Arial", 14, "bold"), fg_color="#1e5228", command=save_settings_action).pack(fill="x", pady=15)

def admin_entry():
    login_window = tk.CTkToplevel(root)
    login_window.title("Admin Verification")
    login_window.geometry("350x200")
    login_window.resizable(False, False)
    login_window.attributes("-topmost", True)
    tk.CTkLabel(login_window, text="Enter Admin Password:", font=("Arial", 14)).pack(pady=15)
    password_entry = tk.CTkEntry(login_window, show="*")
    password_entry.pack(pady=5)

    def attempt_login():
        if password_entry.get() == app_data.get("password", "1234"):
            login_window.destroy()
            open_admin_dashboard()
        else:
            messagebox.showerror("Access Denied", "Incorrect password entry.", parent=login_window)

    tk.CTkButton(login_window, text="Unlock Controls", command=attempt_login).pack(pady=15)

def view_candidates_window():
    view_win = tk.CTkToplevel(root)
    view_win.title("Registered Candidates Ledger")
    view_win.geometry("700x600")
    view_win.resizable(False, False)
    view_win.attributes("-topmost", True)
    tk.CTkLabel(view_win, text="Registered Candidates (By Post)", font=("Arial", 18, "bold"), text_color="#3b7bb2").pack(pady=15)
    scroll_view = tk.CTkScrollableFrame(view_win, width=660, height=500)
    scroll_view.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    current_candidates = app_data.get("candidates", [])
    current_positions = app_data.get("positions", [])
    if not current_candidates:
        tk.CTkLabel(scroll_view, text="No candidates registered yet.", font=("Arial", 14, "italic")).pack(pady=40)
        return
    for pos in current_positions:
        matching_cands = [c for c in current_candidates if c.get("position") == pos]
        if not matching_cands: continue
        section_frame = tk.CTkFrame(scroll_view, fg_color="#1f2937", corner_radius=6)
        section_frame.pack(fill="x", pady=(10, 5), padx=5)
        tk.CTkLabel(section_frame, text=f"POSITION: {pos.upper()}", font=("Arial", 13, "bold"), text_color="#3b7bb2").pack(anchor="w", padx=10, pady=6)
        for cand in matching_cands:
            cand_row = tk.CTkFrame(scroll_view, fg_color="transparent")
            cand_row.pack(fill="x", pady=4, padx=10)
            thumb_label = tk.CTkLabel(cand_row, text="[No Photo]", width=40, height=40, fg_color="#374151", corner_radius=4)
            thumb_label.pack(side="left", padx=(5, 15))
            img_path = cand.get("image_path", "")
            if img_path and os.path.exists(img_path):
                try:
                    p_img = Image.open(img_path).resize((40, 40), Image.Resampling.LANCZOS)
                    tk_thumb = tk.CTkImage(light_image=p_img, dark_image=p_img, size=(40, 40))
                    thumb_label.configure(image=tk_thumb, text="")
                except Exception: pass
            info_text = f"👤 Name: {cand.get('name', 'Unknown')}   |   Class: {cand.get('candidate_class', 'N/A')} - Section: {cand.get('candidate_section', 'N/A')}"
            tk.CTkLabel(cand_row, text=info_text, font=("Arial", 13)).pack(side="left", anchor="w")
            tk.CTkFrame(scroll_view, height=1, fg_color="#374151").pack(fill="x", padx=15, pady=2)


def open_admin_dashboard():
    global candidate_rows, available_positions, positions_container
    candidate_rows = []
    available_positions = app_data.get("positions", ["SPL", "ASPL"])

    dashboard = tk.CTkToplevel(root)
    dashboard.title("Admin Control Panel")

    # Dynamic Sizing for Laptops
    screen_height = dashboard.winfo_screenheight()
    win_w, win_h = 1150, min(850, screen_height - 100)
    dashboard.geometry(f"{win_w}x{win_h}")
    dashboard.attributes("-topmost", True)

    # --- LEFT PANEL: System & Global Config ---
    left_container = tk.CTkFrame(dashboard, width=340)
    left_container.pack(side="left", fill="both", padx=10, pady=10)

    left_scroll = tk.CTkScrollableFrame(left_container, label_text="System Configuration", fg_color="transparent")
    left_scroll.pack(fill="both", expand=True)

    # 1. Security Section
    tk.CTkLabel(left_scroll, text="Security Settings", font=("Arial", 13, "bold"), text_color="#3b7bb2").pack(
        pady=(10, 5), anchor="w")
    sec_frame = tk.CTkFrame(left_scroll, fg_color="#2b2b2b")
    sec_frame.pack(fill="x", padx=5, pady=5)

    old_p = tk.CTkEntry(sec_frame, placeholder_text="Current PIN", show="*")
    old_p.pack(fill="x", padx=10, pady=5)
    new_p = tk.CTkEntry(sec_frame, placeholder_text="New PIN", show="*")
    new_p.pack(fill="x", padx=10, pady=2)
    ver_p = tk.CTkEntry(sec_frame, placeholder_text="Verify New PIN", show="*")
    ver_p.pack(fill="x", padx=10, pady=2)

    def update_password_action():
        if old_p.get() != app_data["password"]:
            messagebox.showerror("Error", "Current password mismatch.")
            return
        if new_p.get() != ver_p.get():
            messagebox.showerror("Error", "New passwords mismatch.")
            return
        app_data["password"] = new_p.get()
        save_data(app_data)
        messagebox.showinfo("Success", "PIN updated.")

    tk.CTkButton(sec_frame, text="Update Security PIN", height=28, fg_color="#4a4a4a",
                 command=update_password_action).pack(fill="x", padx=10, pady=10)

    # 2. Network & Ledger Section
    tk.CTkLabel(left_scroll, text="Network & Ledger", font=("Arial", 13, "bold"), text_color="#3b7bb2").pack(
        pady=(15, 5), anchor="w")
    net_frame = tk.CTkFrame(left_scroll, fg_color="#2b2b2b")
    net_frame.pack(fill="x", padx=5, pady=5)

    url_entry = tk.CTkEntry(net_frame, placeholder_text="http://IP:PORT/api/vote")
    url_entry.insert(0, CENTRAL_SERVER_URL)
    url_entry.pack(fill="x", padx=10, pady=10)

    def update_url_action():
        global CENTRAL_SERVER_URL
        CENTRAL_SERVER_URL = url_entry.get().strip()
        messagebox.showinfo("Success", "Server URL Updated")

    tk.CTkButton(net_frame, text="Save Server URL", height=28, command=update_url_action).pack(fill="x", padx=10,
                                                                                               pady=(0, 5))
    tk.CTkButton(net_frame, text="View Candidates Ledger", height=28, fg_color="#2b5982",
                 command=view_candidates_window).pack(fill="x", padx=10, pady=5)

    # 3. USB Data Portability Section (IMPROVED ZIP LOGIC)
    tk.CTkLabel(left_scroll, text="USB Portability", font=("Arial", 13, "bold"), text_color="#3b7bb2").pack(
        pady=(15, 5), anchor="w")
    usb_frame = tk.CTkFrame(left_scroll, fg_color="#2b2b2b")
    usb_frame.pack(fill="x", padx=5, pady=5)

    def export_data_pack():
        path = filedialog.asksaveasfilename(defaultextension=".vpkg", filetypes=[("Voting Package", "*.vpkg")])
        if not path: return
        try:
            with zipfile.ZipFile(path, 'w') as z:
                if os.path.exists(DATA_FILE):
                    z.write(DATA_FILE, arcname=DATA_FILE)
                if os.path.exists(IMAGE_DIR):
                    for folder, _, files in os.walk(IMAGE_DIR):
                        for f in files:
                            full_path = os.path.join(folder, f)
                            # Preserve directory structure in zip
                            rel_path = os.path.relpath(full_path, os.path.dirname(IMAGE_DIR))
                            z.write(full_path, arcname=rel_path)
            messagebox.showinfo("Success", "Data Pack Exported to USB.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def import_data_pack():
        path = filedialog.askopenfilename(filetypes=[("Voting Package", "*.vpkg")])
        if not path or not messagebox.askyesno("Import", "This will overwrite all candidates. Continue?"): return
        try:
            with zipfile.ZipFile(path, 'r') as z:
                z.extractall()
            messagebox.showinfo("Success", "Data Imported! Restarting Dashboard...")
            dashboard.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.CTkButton(usb_frame, text="Export Pack to USB", height=28, fg_color="#4a4a4a", command=export_data_pack).pack(
        fill="x", padx=10, pady=5)
    tk.CTkButton(usb_frame, text="Import Pack from USB", height=28, fg_color="#4a4a4a",
                 command=import_data_pack).pack(fill="x", padx=10, pady=5)

    # 4. Positions Management
    tk.CTkLabel(left_scroll, text="Election Positions", font=("Arial", 13, "bold"), text_color="#3b7bb2").pack(
        pady=(15, 5), anchor="w")
    pos_input_frame = tk.CTkFrame(left_scroll, fg_color="transparent")
    pos_input_frame.pack(fill="x", padx=5)

    new_post_entry = tk.CTkEntry(pos_input_frame, placeholder_text="e.g. SPL", width=160)
    new_post_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

    positions_container = tk.CTkScrollableFrame(left_scroll, height=150, label_text="Active Roles")
    positions_container.pack(fill="x", padx=5, pady=10)

    def refresh_candidate_dropdowns():
        items = available_positions if available_positions else ["Define Role First"]
        for row in candidate_rows:
            row["dropdown_widget"].configure(values=items)

    def delete_pos(name):
        if name in available_positions:
            available_positions.remove(name);
            render_positions();
            refresh_candidate_dropdowns()

    def render_positions():
        for w in positions_container.winfo_children(): w.destroy()
        for p in available_positions:
            f = tk.CTkFrame(positions_container, fg_color="transparent")
            f.pack(fill="x", pady=1)
            tk.CTkLabel(f, text=p, font=("Arial", 12)).pack(side="left", padx=5)
            tk.CTkButton(f, text="🗑", width=25, height=20, fg_color="#a83232", command=lambda x=p: delete_pos(x)).pack(
                side="right", padx=5)

    def add_pos():
        p = new_post_entry.get().strip()
        if p and p not in available_positions:
            available_positions.append(p);
            new_post_entry.delete(0, 'end');
            render_positions();
            refresh_candidate_dropdowns()

    tk.CTkButton(pos_input_frame, text="+", width=60, command=add_pos).pack(side="right")
    render_positions()

    # --- RIGHT PANEL: Candidate Management ---
    right_container = tk.CTkFrame(dashboard)
    right_container.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    list_frame = tk.CTkScrollableFrame(right_container, label_text="Candidate Ballots")
    list_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def generate_candidate_row(initial_name="", initial_pos="", initial_class="", initial_section="", initial_img=""):
        row_frame = tk.CTkFrame(list_frame)
        row_frame.pack(fill="x", pady=3, padx=5)

        name_in = tk.CTkEntry(row_frame, placeholder_text="Full Name", width=180)
        name_in.insert(0, initial_name);
        name_in.pack(side="left", padx=5, pady=5)

        cls_in = tk.CTkOptionMenu(row_frame, values=["4", "5", "9", "10", "11", "12"], width=75)
        cls_in.set(initial_class if initial_class else "10");
        cls_in.pack(side="left", padx=2)

        sec_in = tk.CTkOptionMenu(row_frame, values=["A", "B", "C", "D", "E"], width=75)
        sec_in.set(initial_section if initial_section else "A");
        sec_in.pack(side="left", padx=2)

        items = available_positions if available_positions else ["Define Role First"]
        pos_drop = tk.CTkOptionMenu(row_frame, values=items, width=140)
        pos_drop.set(initial_pos if initial_pos in items else items[0])
        pos_drop.pack(side="left", padx=5)

        # --- NEW IMAGE PREVIEW LOGIC ---
        img_preview_lbl = tk.CTkLabel(row_frame, text="No Photo", width=40, height=40, fg_color="#1a1a1a",
                                      corner_radius=4)
        img_preview_lbl.pack(side="left", padx=10)

        row_state = {"name_entry": name_in, "class_dropdown": cls_in, "section_dropdown": sec_in,
                     "dropdown_widget": pos_drop, "assigned_img_path": initial_img}

        def update_preview(path):
            if path and os.path.exists(path):
                try:
                    p_img = Image.open(path).resize((40, 40), Image.Resampling.LANCZOS)
                    ctk_thumb = tk.CTkImage(light_image=p_img, dark_image=p_img, size=(40, 40))
                    img_preview_lbl.configure(image=ctk_thumb, text="")
                    img_preview_lbl.image = ctk_thumb  # Prevent garbage collection
                except:
                    img_preview_lbl.configure(text="Err", image=None)

        # Load thumbnail if image already exists
        if initial_img:
            update_preview(initial_img)

        def pick_img():
            p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
            if p:
                def on_edit_complete(edited_path):
                    row_state["assigned_img_path"] = edited_path
                    update_preview(edited_path)

                ImageEditor(dashboard, p, on_edit_complete)

        tk.CTkButton(row_frame, text="Photo", width=60, height=24, command=pick_img).pack(side="left", padx=2)
        tk.CTkButton(
            row_frame,
            text="🗑",
            width=35,
            height=24,
            fg_color="#a83232",
            hover_color="#7a2222",
            command=lambda r=row_frame, s=row_state: [
                r.destroy(),
                candidate_rows.remove(s) if s in candidate_rows else None
            ]
        ).pack(side="right", padx=5)

        candidate_rows.append(row_state)

    # Load Existing Candidates with Thumbnails
    for c in app_data.get("candidates", []):
        generate_candidate_row(c.get("name"), c.get("position"), c.get("candidate_class"), c.get("candidate_section"),
                               c.get("image_path"))

    # Fixed Footer for Right Panel
    footer_frame = tk.CTkFrame(right_container, fg_color="transparent")
    footer_frame.pack(fill="x", side="bottom", pady=10)

    def save_all():
        dashboard.config(cursor="watch")
        root.update_idletasks()

        try:
            final_candidates = []

            for r in candidate_rows:
                try:
                    if not r["name_entry"].winfo_exists():
                        continue
                except:
                    continue

                name = r["name_entry"].get().strip()
                if not name:
                    continue

                pos = r["dropdown_widget"].get()
                cand_class = r["class_dropdown"].get()
                cand_sec = r["section_dropdown"].get()
                src_path = r["assigned_img_path"]

                dest_path = ""

                if src_path and os.path.exists(src_path):
                    abs_image_dir = os.path.abspath(IMAGE_DIR)
                    abs_src = os.path.abspath(src_path)

                    if abs_src.startswith(abs_image_dir):
                        dest_path = src_path
                    else:
                        ext = os.path.splitext(src_path)[1]
                        safe_name = "".join([c for c in name if c.isalnum()]).rstrip()
                        filename = f"profile_{safe_name}_{int(time.time())}{ext}"
                        dest_path = os.path.join(IMAGE_DIR, filename)

                        try:
                            shutil.copy2(src_path, dest_path)
                        except Exception as e:
                            print(f"Copy error: {e}")
                            dest_path = ""

                final_candidates.append({
                    "name": name,
                    "position": pos,
                    "candidate_class": cand_class,
                    "candidate_section": cand_sec,
                    "image_path": dest_path
                })

            app_data["candidates"] = final_candidates
            app_data["positions"] = available_positions
            save_data(app_data)

            dashboard.config(cursor="")
            messagebox.showinfo("Success", "All configurations saved successfully!", parent=dashboard)
            dashboard.destroy()  # Close admin window

        except Exception as e:
            dashboard.config(cursor="")
            messagebox.showerror("Save Error", f"An error occurred while saving: {str(e)}", parent=dashboard)

    tk.CTkButton(footer_frame, text="➕ Add Candidate Row", font=("Arial", 13, "bold"), height=40,
                 command=generate_candidate_row).pack(side="left", fill="x", expand=True, padx=(5, 10))
    tk.CTkButton(footer_frame, text="💾 SAVE ALL CONFIGURATIONS", font=("Arial", 13, "bold"), height=40,
                 fg_color="#1e5228", hover_color="#14361b", command=save_all).pack(side="right", fill="x", expand=True,
                                                                                   padx=(10, 5))

bg_manager.refresh_welcome()

next_vote_btn = tk.CTkButton(
    root,
    text="TAP TO VOTE",
    font=("Arial", 24, "bold"),
    width=380,
    height=85,
    corner_radius=20,
    border_width=5,
    border_color="#404040",
    fg_color="#2b2b2b",
    hover_color="#353535",
    text_color="#FFFFFF",
    border_spacing=0,
    command=start_voting_session
)
next_vote_btn.place(relx=0.49, rely=0.70, anchor="nw")

utility_tray = tk.CTkFrame(root, fg_color="transparent")
utility_tray.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

tk.CTkButton(utility_tray, text="⚙️", width=110, fg_color="#2b2b2b", hover_color="#3a3a3a", command=settings).pack(side="left", padx=5)
tk.CTkButton(utility_tray, text="🔒", width=110, fg_color="#2b2b2b", hover_color="#3a3a3a", command=admin_entry).pack(side="left", padx=5)

root.mainloop()