import ttkbootstrap as tb
import tkinter as tk
from tkinter import filedialog, messagebox

class MainWindow(tb.Window):
    def __init__(self, controller, lang_dict):
        super().__init__(themename="darkly")
        self.controller = controller
        self.lang = 'en'
        self.lang_dict = lang_dict
        self.status_var = tb.StringVar()
        self.status_var.set(self.lang_dict[self.lang]['status_ready'])
        self.fonts = {
            'en': {
                'main': ("Segoe UI", 12),
                'bold': ("Segoe UI", 13, "bold"),
                'title': ("Segoe UI", 18, "bold")
            },
            'ar': {
                'main': ("Cairo", 13),
                'bold': ("Cairo", 14, "bold"),
                'title': ("Cairo", 20, "bold")
            }
        }

        # Set current_fonts as an instance variable for use in all methods
        self.current_fonts = self.fonts[self.lang]
        self.build_ui()

    def build_ui(self):
        self.title(self.lang_dict[self.lang]['app_title'])
        self.geometry('1000x700')
        self.minsize(800, 500)
        self.resizable(True, True)
        self.style.configure('TFrame', background='#181c1f')
        self.current_fonts = self.fonts[self.lang]
        self.style.configure('TLabel', background='#181c1f', foreground='#fff', font=self.current_fonts['main'])
        self.style.configure('TButton', font=self.current_fonts['main'], borderwidth=0, focusthickness=3, focuscolor='none')
        self.style.configure('Accent.TButton', font=self.current_fonts['bold'], borderwidth=0, focusthickness=3, focuscolor='none', background='#c9b37c', foreground='#222')
        self.style.configure('Success.TButton', font=self.current_fonts['bold'], borderwidth=0, focusthickness=3, focuscolor='none', background='#1fa463', foreground='#fff')
        self.style.configure('Danger.TButton', font=self.current_fonts['bold'], borderwidth=0, focusthickness=3, focuscolor='none', background='#333', foreground='#fff')

        # --- Header ---
        header_frame = tb.Frame(self, bootstyle="dark")
        header_frame.pack(fill=tk.X, pady=(0, 2))
        self.title_label = tb.Label(header_frame, text=self.lang_dict[self.lang]['app_title'], font=self.current_fonts['title'], bootstyle="inverse-dark")
        self.title_label.pack(side=tk.LEFT, padx=10, pady=8)
        self.lang_btn_en = tb.Button(header_frame, text='EN', width=4, bootstyle="secondary-outline", command=lambda: self.controller.on_language_change('en'))
        self.lang_btn_en.pack(side=tk.RIGHT, padx=2)
        self.lang_btn_ar = tb.Button(header_frame, text='AR', width=4, bootstyle="secondary-outline", command=lambda: self.controller.on_language_change('ar'))
        self.lang_btn_ar.pack(side=tk.RIGHT, padx=2)

        # --- Import Button ---
        import_frame = tb.Frame(self, bootstyle="dark")
        import_frame.pack(fill=tk.X, pady=(0, 2))
        self.import_btn = tb.Button(import_frame, text=self.lang_dict[self.lang]['import_files'], bootstyle="accent", padding=10, command=self.controller.on_import_files if self.controller else None)
        self.import_btn.pack(padx=20, pady=8, fill=tk.X)

        # --- File List ---
        files_frame = tb.Labelframe(self, text=self.lang_dict[self.lang]['selected_files'], padding=10, bootstyle="dark")
        files_frame.pack(fill=tk.BOTH, padx=10, pady=2, expand=True)
        self.files_listbox = tk.Listbox(files_frame, height=3, bg="#23272b", fg="#fff", selectbackground="#c9b37c", selectforeground="#222", font=self.current_fonts['main'], relief=tk.FLAT, highlightthickness=0, borderwidth=0)
        self.files_listbox.pack(fill=tk.BOTH, expand=True)

    def update_files_list(self, files):
        self.files_listbox.delete(0, tk.END)
        for f in files:
            self.files_listbox.insert(tk.END, f)

        # --- Audio Player ---
        audio_frame = tb.Labelframe(self, text=self.lang_dict[self.lang]['audio_player'], padding=10, bootstyle="dark")
        audio_frame.pack(fill=tk.BOTH, padx=10, pady=2, expand=True)
        self.waveform = tk.Canvas(audio_frame, width=600, height=60, bg="#23272b", highlightthickness=0, borderwidth=0)
        self.waveform.pack(pady=5, fill=tk.X, expand=True)
        controls_frame = tb.Frame(audio_frame, bootstyle="dark")
        controls_frame.pack()
        for sym in ['⏮', '⏪', '⏯', '⏩', '⏭']:
            tb.Button(controls_frame, text=sym, width=3, bootstyle="secondary-outline", state=tk.DISABLED).pack(side=tk.LEFT, padx=2)
        self.audio_time = tb.Label(audio_frame, text='02:15 / 45:00', font=self.current_fonts['main'], bootstyle="inverse-dark")
        self.audio_time.pack(side=tk.RIGHT, padx=10)

        # --- Recommended Cuts & Edit Cut ---
        cuts_frame = tb.Frame(self, bootstyle="dark")
        cuts_frame.pack(fill=tk.BOTH, padx=10, pady=2, expand=True)
        rec_frame = tb.Labelframe(cuts_frame, text=self.lang_dict[self.lang]['recommended_cuts'], padding=10, bootstyle="dark")
        rec_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cuts_listbox = tk.Listbox(rec_frame, height=5, bg="#23272b", fg="#fff", selectbackground="#c9b37c", selectforeground="#222", font=self.current_fonts['main'], relief=tk.FLAT, highlightthickness=0, borderwidth=0)
        self.cuts_listbox.pack(fill=tk.BOTH, expand=True)
        for i, (start, end, label) in enumerate([
            ("00:00", "05:30", "Intro / بداية"),
            ("05:30", "15:10", "Rakah 1"),
            ("15:10", "25:40", "Rakah 2"),
            ("25:40", "35:00", "Rakah 3")]):
            self.cuts_listbox.insert(tk.END, f"{i+1}) {start} → {end} ({label})")
        self.restore_btn = tb.Button(rec_frame, text=self.lang_dict[self.lang]['restore_recommended'], bootstyle="secondary-outline", state=tk.DISABLED)
        self.restore_btn.pack(pady=5)
        edit_frame = tb.Labelframe(cuts_frame, text=self.lang_dict[self.lang]['edit_cut'], padding=10, bootstyle="dark")
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        tb.Label(edit_frame, text=self.lang_dict[self.lang]['start']).grid(row=0, column=0, sticky='e', pady=2)
        self.start_entry = tb.Entry(edit_frame, width=8, font=self.current_fonts['main'])
        self.start_entry.grid(row=0, column=1, pady=2)
        self.start_entry.insert(0, "05:30")
        tb.Label(edit_frame, text=self.lang_dict[self.lang]['end']).grid(row=1, column=0, sticky='e', pady=2)
        self.end_entry = tb.Entry(edit_frame, width=8, font=self.current_fonts['main'])
        self.end_entry.grid(row=1, column=1, pady=2)
        self.end_entry.insert(0, "15:10")
        self.set_from_player_btn = tb.Button(edit_frame, text=self.lang_dict[self.lang]['set_from_player'], bootstyle="secondary-outline", state=tk.DISABLED)
        self.set_from_player_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # --- Export & Cancel Buttons ---
        action_frame = tb.Frame(self, bootstyle="dark")
        action_frame.pack(fill=tk.X, padx=10, pady=8)
        self.export_btn = tb.Button(action_frame, text=self.lang_dict[self.lang]['export_selected'], bootstyle="success", state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cancel_btn = tb.Button(action_frame, text=self.lang_dict[self.lang]['cancel'], bootstyle="danger", state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- Status Bar ---
        self.status_bar = tb.Label(self, textvariable=self.status_var, bootstyle="inverse-dark")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, text):
        self.status_var.set(text)

    def toggle_lang(self):
        self.lang = 'ar' if self.lang == 'en' else 'en'
        self.controller.on_language_change(self.lang)

    # ...other UI methods as needed...
