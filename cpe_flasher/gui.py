from __future__ import annotations

import os
import queue
import sys
import threading
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .core import prepare_flash, install_flash, restore_backup, locate_games, FlashOptions
from cpeloader import write_json
from .nuttyroot import NuttyRootInputs


class FlasherApp(tk.Tk):
    def __init__(self, show_warning=True):
        super().__init__()
        self.title('CPE Flasher Tool')
        self.geometry('1180x820')
        self.minsize(980, 720)
        self.configure(bg='#0b1020')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#141c2f')
        style.configure('TLabel', background='#141c2f', foreground='#e8edf6', font=('Segoe UI', 10))
        style.configure('Muted.TLabel', foreground='#9aabc3')
        style.configure('Title.TLabel', font=('Segoe UI', 26, 'bold'), foreground='#f4f7ff')
        style.configure('Section.TLabel', font=('Segoe UI', 13, 'bold'))
        style.configure('TButton', font=('Segoe UI', 10), padding=(14, 9), background='#25324b', foreground='#e8edf6', borderwidth=0)
        style.map('TButton', background=[('active', '#34445f')], foreground=[('disabled', '#728199')])
        style.configure('Primary.TButton', background='#8884ff', foreground='#0b1020', font=('Segoe UI', 10, 'bold'))
        style.map('Primary.TButton', background=[('active', '#a7a3ff'), ('disabled', '#25324b')])
        style.configure('TEntry', fieldbackground='#0e1628', foreground='#e8edf6', insertcolor='#e8edf6', bordercolor='#33415b', padding=8)
        style.configure('TCheckbutton', background='#141c2f', foreground='#e8edf6', font=('Segoe UI', 10), padding=4)
        style.map('TCheckbutton', background=[('active', '#141c2f')], foreground=[('disabled', '#728199')])
        style.configure('TNotebook', background='#141c2f', borderwidth=0, tabmargins=(0, 0, 0, 8))
        style.configure('TNotebook.Tab', background='#1d2940', foreground='#9aabc3', padding=(15, 11), font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#8884ff')], foreground=[('selected', '#0b1020')])
        style.configure('Horizontal.TProgressbar', background='#8884ff', troughcolor='#25324b', borderwidth=0)
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
        try: self.iconbitmap(str(root/'icon.ico'))
        except tk.TclError: pass
        self.events = queue.Queue()
        self.busy = False
        self.plan = None
        self.last_backup = None
        self.archive = tk.StringVar()
        self.target = tk.StringVar()
        self.project = tk.StringVar()
        self.source = tk.StringVar(value=str(root) if (root/'cube_core.py').exists() else '')
        local_python = root/'.venv'/'Scripts'/'python.exe'
        self.python = tk.StringVar(value=str(local_python) if local_python.is_file() else ('' if getattr(sys, 'frozen', False) else sys.executable))
        self.trust = tk.BooleanVar(value=False)
        self.userdata = tk.StringVar()
        self.loader = tk.StringVar()
        self.scripts = ()
        self.script_status = tk.StringVar(value='No optional startup scripts selected.')
        self.verbose = tk.BooleanVar(value=False)
        self.safety_alerts = tk.BooleanVar(value=False)
        self.full_rewrite = tk.BooleanVar(value=True)
        self.nuttyroot = tk.BooleanVar(value=False)
        self.nutty_zip = tk.StringVar()
        self.nutty_cp = tk.StringVar()
        self.rootmode_tar = tk.StringVar()
        self.nutty_verify = tk.StringVar()
        self.official_sha = tk.StringVar()
        content = ttk.Frame(self, padding=24)
        content.pack(fill='both', expand=True)
        header = ttk.Frame(content); header.pack(fill='x', pady=(0, 22))
        mark = tk.Canvas(header, width=48, height=48, bg='#141c2f', highlightthickness=0)
        mark.pack(side='left', padx=(0, 14))
        mark.create_polygon(24, 3, 44, 14, 24, 26, 4, 14, fill='#aaa7ff')
        mark.create_polygon(4, 17, 22, 28, 22, 46, 4, 35, fill='#6864d9')
        mark.create_polygon(26, 28, 44, 17, 44, 35, 26, 46, fill='#8884ff')
        heading = ttk.Frame(header); heading.pack(side='left')
        ttk.Label(heading, text='CPE Flasher Tool', style='Title.TLabel').pack(anchor='w')
        ttk.Label(heading, text='Engine customization. A controlled rebuild. A way back.', style='Muted.TLabel').pack(anchor='w', pady=(2, 0))
        ttk.Label(header, text='WINDOWS  /  v1.1.0', style='Muted.TLabel').pack(side='right')
        self.controls = []
        workspace = ttk.Frame(content); workspace.pack(fill='both', expand=True)
        workspace.columnconfigure(0, weight=3); workspace.columnconfigure(1, weight=1, minsize=270)
        workspace.rowconfigure(0, weight=1)
        notebook = ttk.Notebook(workspace); notebook.grid(row=0, column=0, sticky='nsew', padx=(0, 20))
        self.notebook = notebook
        inputs = self.scroll_page(notebook, '01  Game & compiler')
        options = self.scroll_page(notebook, '02  Userdata & loaders')
        nutty = self.scroll_page(notebook, '03  NuttyMod Root')
        activity = ttk.Frame(workspace, padding=(16, 12)); activity.grid(row=0, column=1, sticky='nsew')
        ttk.Label(activity, text='ACTIVITY', style='Section.TLabel').pack(anchor='w')
        ttk.Label(activity, text='Build output and recovery history', style='Muted.TLabel').pack(anchor='w', pady=(4, 12))
        self.log_box = tk.Text(activity, width=28, height=10, bg='#0b1020', fg='#b9c7df', insertbackground='white', font=('Consolas', 9), relief='flat', padx=12, pady=12, wrap='word', state='disabled')
        self.log_box.pack(fill='both', expand=True)
        ttk.Label(activity, text='01  Configure the inputs\n02  Build in an isolated staging folder\n03  Confirm installation\n04  Restore a backup if needed', style='Muted.TLabel', justify='left').pack(anchor='w', pady=(16, 0))
        enabled = ttk.Checkbutton(nutty, text='Flash NuttyMod Root under userdata (requires every file below)', variable=self.nuttyroot)
        enabled.pack(anchor='w', pady=8); self.controls.append(enabled)
        ttk.Label(nutty, text='Select nuttymod_loader.py on tab 02, then add the matching package files here. Root Mode requires Full rewrite.', wraplength=560, style='Muted.TLabel').pack(anchor='w', pady=8)
        self.row(nutty, 'NuttyMod loader folder ZIP', self.nutty_zip, lambda: self.pick_file(self.nutty_zip, '*.zip'))
        self.row(nutty, 'CP — nuttymod_root.tar', self.nutty_cp, lambda: self.pick_file(self.nutty_cp, '*.tar'))
        self.row(nutty, 'Required Root Mode library — rootmode.tar', self.rootmode_tar, lambda: self.pick_file(self.rootmode_tar, '*.tar'))
        self.row(nutty, 'Userdata — nuttymod_cube_verifycation.tar', self.nutty_verify, lambda: self.pick_file(self.nutty_verify, '*.tar'))
        self.row(nutty, 'SHA256SUMS.txt from the official portable release', self.official_sha, lambda: self.pick_file(self.official_sha, '*.txt'))
        ttk.Label(nutty, text='Hashes check consistency, not authorship. Use official releases and trusted packages. Legacy bytecode loaders are incompatible.', wraplength=560, style='Muted.TLabel').pack(anchor='w', pady=8)
        self.row(inputs, '1. Original Cube Beta portable ZIP', self.archive, self.pick_zip)
        self.row(inputs, '2. Installed Cube Beta folder', self.target, lambda: self.pick_folder(self.target))
        locate = ttk.Button(inputs, text='Locate installed game', command=self.locate)
        locate.pack(anchor='w', pady=(0, 10)); self.controls.append(locate)
        self.row(inputs, '3. CPE project folder (leave blank for bundled Rephysics)', self.project, lambda: self.pick_folder(self.project))
        self.row(inputs, '4. Complete game source (blank: use source inside portable ZIP)', self.source, lambda: self.pick_folder(self.source))
        self.row(inputs, '5. Python 3.12 with Pygame, Pymunk and PyInstaller installed', self.python, self.pick_python)
        self.row(options, '6. Required userdata folder (game-level root configuration)', self.userdata, lambda: self.pick_folder(self.userdata))
        create = ttk.Button(options, text='Create userdata folder…', command=self.create_userdata)
        create.pack(anchor='w', pady=(0, 8)); self.controls.append(create)
        self.row(options, '7. Optional custom mod / add-on loader (.py)', self.loader, self.pick_loader)
        scripts = ttk.Button(options, text='Choose optional Python startup scripts…', command=self.pick_scripts)
        scripts.pack(anchor='w'); self.controls.append(scripts)
        clear = ttk.Button(options, text='Clear custom loader / scripts', command=self.clear_hooks)
        clear.pack(anchor='w'); self.controls.append(clear)
        ttk.Label(options, textvariable=self.script_status, wraplength=560, style='Muted.TLabel').pack(anchor='w', pady=6)
        for label, variable in (('VP: verbose Python console / imports and userdata log', self.verbose),
                                ('Safety Cube cosmetic alerts (integrity warnings stay on)', self.safety_alerts),
                                ('Full rewrite / back up obsolete managed files', self.full_rewrite)):
            check = ttk.Checkbutton(options, text=label, variable=variable)
            check.pack(anchor='w', pady=4); self.controls.append(check)
        footer = ttk.Frame(content); footer.pack(fill='x', pady=(16, 0))
        consent = ttk.Checkbutton(footer, text='I trust the selected ZIP, source, engine, userdata, loaders and scripts.', variable=self.trust)
        consent.pack(anchor='w', pady=(8, 5)); self.controls.append(consent)
        ttk.Label(footer, text='Unlock: Ctrl+A → Y. Close the game before install or restore. Backups: backup/cpe-flasher.', style='Muted.TLabel').pack(anchor='w', pady=(4, 12))
        actions = ttk.Frame(footer)
        actions.pack(fill='x')
        prepare = ttk.Button(actions, text='Flash ZIP + Recompile', style='Primary.TButton', command=self.prepare)
        prepare.pack(side='left'); self.controls.append(prepare)
        self.install_button = ttk.Button(actions, text='Replace game + Create shortcut', command=self.install, state='disabled')
        self.install_button.pack(side='left', padx=10)
        recovery_actions = ttk.Frame(actions); recovery_actions.pack(side='right')
        for label, callback in (('Undo changes', self.undo_changes), ('Restore backup…', self.restore)):
            button = ttk.Button(recovery_actions, text=label, command=callback)
            button.pack(side='left', padx=(0, 10)); self.controls.append(button)
        self.progress = ttk.Progressbar(footer, mode='indeterminate')
        self.progress.pack(fill='x', pady=(14, 8))
        self.status = tk.StringVar(value='READY  /  Configure your game inputs to begin. Installed files remain untouched until you confirm.')
        ttk.Label(footer, textvariable=self.status, wraplength=1000, style='Muted.TLabel').pack(anchor='w')
        self.after(100, self.drain)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.locate(silent=True)
        for variable in (self.archive, self.target, self.project, self.source, self.python,
                         self.userdata, self.loader, self.verbose, self.safety_alerts, self.full_rewrite,
                         self.nuttyroot, self.nutty_zip, self.nutty_cp, self.nutty_verify, self.official_sha, self.rootmode_tar):
            variable.trace_add('write', self.invalidate_plan)
        if show_warning: self.after_idle(self.startup_warning)

    def scroll_page(self, notebook, title):
        page = ttk.Frame(notebook)
        notebook.add(page, text=title)
        canvas = tk.Canvas(page, bg='#141c2f', highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y'); canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        body = ttk.Frame(canvas, padding=(4, 12, 16, 12))
        window = canvas.create_window((0, 0), window=body, anchor='nw')
        body.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
        def wheel(event):
            canvas.yview_scroll(-int(event.delta/120), 'units')
            return 'break'
        canvas.bind('<MouseWheel>', wheel)
        # Bind descendants after construction; no global mouse-wheel hooks.
        def bind_children(widget):
            widget.bind('<MouseWheel>', wheel)
            for child in widget.winfo_children(): bind_children(child)
        self.after_idle(lambda: bind_children(body))
        return body

    def invalidate_plan(self, *args):
        if self.busy: return
        self.plan = None
        self.install_button.configure(state='disabled')

    def startup_warning(self):
        messagebox.showwarning('CPE Flasher Tool — corruption warning',
            'Not following these steps may corrupt The Cube Beta.\n\n'
            '1. Keep an original portable ZIP and backups.\n2. Unlock CPELoader (Ctrl+A → Y), then close the game.\n'
            '3. Choose required userdata and a working Python compiler.\n4. Only select trusted loaders/scripts.\n'
            '5. Wait for compilation to finish before replacing the game folder.\n\n'
            'Root means game customization, NOT Windows administrator access. '
            'The flashed ZIP stays unlocked and shows CPELoader warnings.')

    def create_userdata(self):
        selected = filedialog.askdirectory(title='Choose a folder for userdata')
        if not selected: return
        folder = Path(selected)
        if not (folder/'userdata.json').exists():
            try: write_json(folder/'userdata.json', {'schema': 1, 'player_name': 'Cube Player'})
            except OSError as exc: messagebox.showerror('Userdata', str(exc)); return
        self.userdata.set(str(folder))

    def pick_loader(self):
        selected = filedialog.askopenfilename(title='Trusted custom loader', filetypes=[('Python scripts', '*.py')])
        if selected: self.loader.set(selected)

    def pick_scripts(self):
        selected = filedialog.askopenfilenames(title='Trusted Python startup scripts', filetypes=[('Python scripts', '*.py')])
        if selected:
            self.scripts = tuple(Path(path) for path in selected)
            self.script_status.set(', '.join(path.name for path in self.scripts))
            self.invalidate_plan()

    def clear_hooks(self):
        self.loader.set(''); self.scripts = (); self.script_status.set('No optional startup scripts selected.')

    def row(self, parent, label, variable, browse):
        ttk.Label(parent, text=label).pack(anchor='w')
        row = ttk.Frame(parent); row.pack(fill='x', pady=(3, 8))
        entry = ttk.Entry(row, textvariable=variable); entry.pack(side='left', fill='x', expand=True)
        button = ttk.Button(row, text='Browse…', command=browse); button.pack(side='left', padx=(8, 0))
        self.controls.extend((entry, button))

    def pick_zip(self):
        selected = filedialog.askopenfilename(filetypes=[('Portable ZIP', '*.zip')])
        if selected: self.archive.set(selected)

    def pick_folder(self, variable):
        selected = filedialog.askdirectory()
        if selected: variable.set(selected)

    def pick_python(self):
        selected = filedialog.askopenfilename(title='Select python.exe', filetypes=[('Python executable', '*.exe')])
        if selected: self.python.set(selected)

    def pick_file(self, variable, pattern):
        selected = filedialog.askopenfilename(filetypes=[('Package file', pattern)])
        if selected: variable.set(selected)

    def locate(self, silent=False):
        found = locate_games()
        if found: self.target.set(str(found[0]))
        elif not silent: messagebox.showinfo('Game not found', 'Use Browse to choose the folder containing The Cube Beta Halloween Update.exe.')

    def log(self, message): self.events.put(('log', message))

    def start(self, operation):
        self.busy = True
        for control in self.controls: control.configure(state='disabled')
        self.install_button.configure(state='disabled')
        self.progress.start()
        def worker():
            try: self.events.put(('done', operation()))
            except Exception as exc: self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def prepare(self):
        if not self.trust.get():
            messagebox.showwarning('Trust required', 'Only flash projects and game sources you trust. Select the trust checkbox to proceed.'); return
        if not all(value.get().strip() for value in (self.archive, self.target, self.python, self.userdata)):
            messagebox.showwarning('Missing input', 'Select a portable ZIP, target game folder, Python interpreter and required userdata folder.'); return
        if not messagebox.askyesno('Build trusted code?', 'The compiler can execute Python from the selected source and project. Continue only if you trust those files?'): return
        archive, target, python = (Path(value.get()) for value in (self.archive, self.target, self.python))
        source = Path(self.source.get()) if self.source.get().strip() else None
        project = Path(self.project.get()) if self.project.get().strip() else None
        options = FlashOptions(Path(self.userdata.get()), Path(self.loader.get()) if self.loader.get().strip() else None,
                               self.scripts, self.verbose.get(), self.safety_alerts.get(), self.full_rewrite.get())
        if self.nuttyroot.get():
            if not all(v.get().strip() for v in (self.loader, self.nutty_zip, self.nutty_cp, self.nutty_verify, self.official_sha, self.rootmode_tar)):
                messagebox.showwarning('NuttyMod Root', 'Select the loader .py, folder ZIP, all three TAR files, and official SHA256SUMS.txt. Root Mode requires Full rewrite.'); return
            options.nuttymod_root = NuttyRootInputs(*(Path(v.get()) for v in (self.nutty_zip, self.nutty_cp, self.nutty_verify, self.official_sha, self.rootmode_tar)))
        local = Path(os.environ.get('LOCALAPPDATA', str(Path.home())))
        workspace = local/'CPEFlasherTool'/'staging'/uuid.uuid4().hex
        self.plan = None
        self.status.set('Flashing and compiling in staging. The installed game is untouched.')
        self.start(lambda: ('prepared', prepare_flash(archive, target, workspace, source, project, python, self.log, options=options)))

    def install(self):
        if self.plan is None: return
        if not messagebox.askyesno('Replace game files?', f'Close The Cube Beta first.\n\nTarget: {self.plan.target}\n\nBack up and replace the game with the rebuilt portable folder?'):
            return
        plan = self.plan
        self.status.set('Backing up and replacing the game…')
        self.start(lambda: ('installed', install_flash(plan, self.log)))

    def undo_changes(self):
        if self.last_backup is not None:
            self.restore(self.last_backup)
        else:
            self.plan = None
            self.install_button.configure(state='disabled')
            self.status.set('Prepared changes discarded; installed game untouched. Use Restore backup for an earlier flash.')

    def restore(self, backup=None):
        if not self.target.get().strip():
            messagebox.showwarning('Restore backup', 'Select the target game folder first.'); return
        target = Path(self.target.get()).resolve()
        if backup is None:
            selected = filedialog.askdirectory(title='Choose the timestamped backup containing manifest.json', initialdir=str(target/'backup'/'cpe-flasher'))
            if not selected: return
            backup = Path(selected)
        if not messagebox.askyesno('Restore game backup?', f'Close The Cube Beta first.\n\nGame: {target}\nBackup: {backup}\n\nRestore recorded files and remove files added by that flash? Current affected files will be backed up before restoration. Unrelated saves are preserved.'):
            return
        self.plan = None
        self.status.set('Saving current files and restoring the selected backup…')
        self.start(lambda: ('restored', restore_backup(target, backup, self.log)))

    def drain(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'log':
                    self.log_box.configure(state='normal'); self.log_box.insert('end', value+'\n'); self.log_box.see('end'); self.log_box.configure(state='disabled')
                else:
                    self.busy = False; self.progress.stop()
                    for control in self.controls: control.configure(state='normal')
                    if kind == 'error':
                        self.status.set(value); messagebox.showerror('CPE Flasher Tool', value)
                    elif value[0] == 'prepared':
                        self.plan = value[1]
                        self.status.set(f'Rebuild succeeded. Flashed ZIP: {self.plan.output_zip}')
                    elif value[0] == 'restored':
                        self.last_backup = None
                        self.plan = None
                        self.status.set(f'Backup restored. Pre-restore recovery snapshot: {value[1]}')
                        messagebox.showinfo('Restore complete', self.status.get())
                    else:
                        self.last_backup = value[1]
                        self.plan = None
                        self.status.set(f'Installed successfully. Backup: {value[1]}. Shortcut is inside the game folder.')
                        messagebox.showinfo('Flash complete', self.status.get())
                    self.install_button.configure(state='normal' if self.plan is not None else 'disabled')
        except queue.Empty: pass
        self.after(100, self.drain)

    def close(self):
        if self.busy:
            messagebox.showwarning('Operation in progress', 'Wait until the build or file replacement finishes before closing.'); return
        self.destroy()


def main(): FlasherApp().mainloop()
