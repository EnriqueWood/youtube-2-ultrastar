import os
import subprocess
import sys
import threading
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

ULTRAS_FLAGS = {
    'whisper': ['tiny','base','small','medium','large-v1','large-v2','large-v3',
                'tiny.en','base.en','small.en','medium.en'],
    'whisper_align_model': None,
    'language': ['en','fr','de','es','it','ja','zh','nl','uk','pt'],
    'whisper_batch_size': None,
    'whisper_compute_type': ['float16','int8'],
    'keep_numbers': None,
    'crepe': ['tiny','full'],
    'crepe_step_size': None,
    'disable_hyphenation': None,
    'disable_separation': None,
    'disable_karaoke': None,
    'create_audio_chunks': None,
    'keep_cache': None,
    'plot': None,
    'format_version': ['0.3.0','1.0.0','1.1.0','1.2.0','2.0.0'],
    'musescore_path': None,
    'ffmpeg': None,
    'cookiefile': None,
    'force_cpu': None,
    'force_whisper_cpu': None,
    'force_crepe_cpu': None
}

class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('YouTube-2-UltraStar (UltraSinger Wrapper)')
        self.resizable(True, True)
        self.grid_columnconfigure(0, weight=1)

        # Input
        tk.Label(self, text='Input (YouTube URL or local MP3/MP4):').grid(column=0, row=0, padx=10, pady=5, sticky='w')
        self.src = tk.StringVar()
        tk.Entry(self, textvariable=self.src, width=60).grid(column=0, row=1, padx=10)

        # Status
        self.status_var = tk.StringVar(value='Ready')
        ttk.Label(self, textvariable=self.status_var).grid(column=0, row=2, padx=10, sticky='w')

        # Progress bar
        self.progress = ttk.Progressbar(self, mode='determinate', maximum=100)
        self.progress.grid(column=0, row=3, padx=10, pady=(0,5), sticky='we')
        self.progress['value'] = 0

        # Advanced toggle
        self.adv = False
        btn = ttk.Button(self, text='Show Advanced Options', command=self.toggle)
        btn.grid(column=0, row=4, padx=10, pady=5, sticky='w')
        self.adv_btn = btn

        # Advanced flags frame
        self.container = ttk.Frame(self)
        self.container.grid(column=0, row=5, padx=10, sticky='nsew')
        self.container.grid_forget()
        self.container.grid_columnconfigure(0, weight=1)

        # Scrolling canvas
        self.canvas = tk.Canvas(self.container, height=200)
        self.scroll = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid(row=0, column=1, sticky="ns")

        # Inner frame
        self.frame = ttk.Frame(self.canvas)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame_window = self.canvas.create_window((0,0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.frame_window, width=e.width))
        self.vars, self.widgets = {}, {}

        row = 0
        for f, opts in ULTRAS_FLAGS.items():
            v = tk.BooleanVar()
            chk = ttk.Checkbutton(self.frame, text=f, variable=v, command=lambda f=f: self.toggle_flag(f))
            chk.grid(column=0, row=row, sticky='w', padx=5)
            self.vars[f] = v
            if opts:
                dd = ttk.Combobox(self.frame, values=opts, state='disabled')
                dd.grid(column=1, row=row, padx=5, sticky='ew')
                self.widgets[f] = dd
            row += 1

        # Log display
        self.log_frame = ttk.LabelFrame(self, text="Logs")
        self.log_frame.grid(column=0, row=6, padx=10, pady=5, sticky='nsew')
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_display = scrolledtext.ScrolledText(self.log_frame, height=10, wrap=tk.WORD)
        self.log_display.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')
        self.log_display.config(state=tk.DISABLED)

        self.convert_btn = ttk.Button(self, text='Convert', command=self.start_conversion)
        self.convert_btn.grid(column=0, row=7, columnspan=2, pady=10, sticky='ew')

        self.config_file = os.path.join(self.get_user_config_dir(), '.youtube2ultrastar.conf')
        self.load_config()

        # Menu bar
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save Options", command=self.save_config)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def toggle(self):
        if not self.adv:
            self.container.grid(column=0, row=5, padx=10, sticky='nsew')
            self.adv_btn.config(text='Hide Advanced Options')
        else:
            self.container.grid_remove()
            self.adv_btn.config(text='Show Advanced Options')
        self.adv = not self.adv

    def toggle_flag(self, flag):
        w = self.widgets.get(flag)
        if self.vars[flag].get() and w:
            w.config(state='readonly')
            w.set(ULTRAS_FLAGS[flag][0])
        elif w:
            w.config(state='disabled')

    def _append_log(self, text):
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, text)
        self.log_display.see(tk.END)
        self.log_display.config(state=tk.DISABLED)

    def check_docker(self):
        try:
            subprocess.check_output(['docker','--version'])
            subprocess.check_output(['docker','compose','version'])
            return True
        except Exception:
            return False

    def get_user_config_dir(self):
        if sys.platform.startswith('win'):
            return os.getenv('APPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            return os.path.expanduser('~/Library/Application Support')
        else:
            return os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

    def load_config(self):
        if os.path.isfile(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'): continue
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip()
                            val = val.strip()
                            if key in self.vars:
                                self.vars[key].set(True)
                                widget = self.widgets.get(key)
                                if widget:
                                    widget.config(state='readonly')
                                    widget.set(val)
            except Exception as e:
                print(f"Failed to load config: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                for key, var in self.vars.items():
                    if key == 'language':
                        continue  # skip language

                    var_enabled = var.get()
                    widget = self.widgets.get(key)

                    if var_enabled:
                        # Option is enabled
                        if widget and widget.get():
                            # Save with dropdown value
                            f.write(f"{key}={widget.get()}\n")
                        else:
                            # Save as true for checkboxes without dropdowns
                            f.write(f"{key}=true\n")
                    else:
                        # Save disabled state explicitly
                        f.write(f"#{key}=false\n")

            messagebox.showinfo("Saved", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def show_docker_prompt(self):
        popup = tk.Toplevel(self)
        popup.title("Docker Required")
        popup.geometry("400x160")
        popup.resizable(False, False)
        tk.Label(popup, text="You need to install Docker before continuing.", wraplength=380).pack(pady=10)

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=5)

        confirmed = {'value': False}
        canceled = {'value': False}

        def open_docker_download():
            import webbrowser
            webbrowser.open('https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe')

        def check_again():
            if self.check_docker():
                confirmed['value'] = True
                popup.destroy()
            else:
                messagebox.showwarning("Not Found", "Docker is still not installed.")

        def cancel():
            canceled['value'] = True
            popup.destroy()

        ttk.Button(btn_frame, text="Install Docker", command=open_docker_download).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Check Again", command=check_again).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=cancel).grid(row=0, column=2, padx=5)

        self.wait_window(popup)
        return confirmed['value'] and not canceled['value']

    def start_conversion(self):
        self.log_display.config(state=tk.NORMAL)
        self.log_display.delete('1.0', tk.END)
        self.log_display.config(state=tk.DISABLED)
        self.convert_btn.config(state='disabled', text='Processing...')
        self.progress['value'] = 0
        threading.Thread(target=self.convert, daemon=True).start()

    def run_logged(self, cmd, label, cwd=None):
        """Run cmd as subprocess, set status to label, stream output to both log widget and console."""
        self.status_var.set(label)
        proc = subprocess.Popen(cmd,
                                cwd=cwd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                bufsize=1)  # line-buffered
        for raw in proc.stdout:
            print(raw, end='')
            # strip ANSI color codes
            clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)
            msg = clean if clean.endswith('\n') else clean + '\n'
            self.after(0, self._append_log, msg)


        ret = proc.wait()
        if ret != 0:
            raise subprocess.CalledProcessError(ret, cmd)

    def convert(self):
        src = self.src.get().strip()
        if not src:
            self.after(0, messagebox.showerror, 'Error', 'Enter valid input')
            self.after(0, self._reset_ui, False)
            return

        # Normalize YouTube URL
        if src.startswith(('http://','https://')):
            try:
                parts = urlparse(src)
                qs = parse_qs(parts.query)
                if 'v' in qs and qs['v']:
                    new_q = urlencode({'v': qs['v'][0]})
                    parts = parts._replace(query=new_q)
                    src = urlunparse(parts)
                else:
                    parts = parts._replace(query='')
                src = urlunparse(parts)
            except:
                pass

        # Docker check loop
        self.status_var.set('Checking Docker...')
        if not self.check_docker():
            if not self.show_docker_prompt():
                self._reset_ui()
                return

        # Flags
        self.status_var.set('Preparing flags...')
        flags = []
        for f, v in self.vars.items():
            if v.get():
                if f in self.widgets:
                    val = self.widgets[f].get()
                    flags += [f"--{f}", val]
                else:
                    flags += [f"--{f}"]

        # Write compose file
        self.status_var.set('Writing compose file...')
        wd = os.getcwd()
        songs = os.path.join(wd,'songs')
        os.makedirs(songs, exist_ok=True)
        for d in ['output','cache','local','torch_ext']:
            os.makedirs(os.path.join(songs,d), exist_ok=True)
        yml = f"""services:
  ultrasinger:
    container_name: UltraSinger
    image: rakuri255/ultrasinger:latest
    stdin_open: true
    tty: true
    user: root
    volumes:
      - {songs}/output:/app/UltraSinger/src/output
      - {songs}/cache:/root/.cache
      - {songs}/torch_ext:/app/UltraSinger/src/torch_ext
      - {songs}/local:/root/.local
    environment:
      - XDG_CACHE_HOME=/root/.cache
      - TORCH_HOME=/root/.cache/torch
      - TRANSFORMERS_CACHE=/root/.cache/huggingface/hub
      - MPLCONFIGDIR=/root/.cache/matplotlib
      - TORCH_EXTENSIONS_DIR=/app/UltraSinger/src/torch_ext
      - XDG_DATA_HOME=/root/.local
"""
        with open(os.path.join(songs,'compose-nogpu.yml'),'w') as f:
            f.write(yml)

        # Start container
        self.run_logged(
            ['docker','compose','-f','compose-nogpu.yml','up','-d','--force-recreate'],
            'Starting container...',
            cwd=songs
        )
        # Install MuseScore
        self.run_logged(
            [
                'docker','exec','-u','root','UltraSinger','bash','-lc',
                "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y musescore3 && apt-get clean"
            ],
            'Installing MuseScore...',
            cwd=songs
        )
        # Run conversion with log monitoring
        self.status_var.set('Converting...')
        cmd = ['docker','exec','-u','root','UltraSinger','bash','-lc',
               f"cd /app/UltraSinger/src && python UltraSinger.py -i '{src}' {' '.join(flags)}"]
        proc = subprocess.Popen(cmd, cwd=songs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        item_pattern = re.compile(r"Downloading item (\d+) of (\d+)")
        download_pct_pattern = re.compile(r"^\[download\]\s*([0-9]+(?:\.[0-9]+)?)%")
        demucs_pct_pattern = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)%")
        slash_pct_pattern = re.compile(r"^\s*(\d+)\s*/\s*(\d+)")  # new heuristic
        generic_pct_pattern = re.compile(r"([0-9]+(?:\.[0-9]+)?)%")
        last_label = 'Working'
        for raw in proc.stdout:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", raw)
            msg = clean if clean.endswith('\n') else clean + '\n'
            self.after(0, self._append_log, msg)
            # update on item downloads
            m_item = item_pattern.search(clean)
            if m_item:
                cur, tot = map(int, m_item.groups())
                pct = int(cur / tot * 100)
                self.progress['value'] = pct
                self.status_var.set(f"Downloading item {cur} of {tot}")
                msg = f"[DEBUG] Item download: {pct}%"
                self.after(0, self._append_log, msg)
            else:
                # slash-based counts (e.g. 1/552)
                m_slash = slash_pct_pattern.match(clean)
                if m_slash:
                    cur, tot = map(int, m_slash.groups())
                    pct = int(cur / tot * 100)
                    self.progress['value'] = pct
                    self.status_var.set(last_label)
                    msg = f"[DEBUG] Slash progress: {pct}%, label: '{last_label}'"
                    self.after(0, self._append_log, msg)
                else:
                    # youtube-dl download percentages or demucs
                    m_dl = download_pct_pattern.match(clean)
                    m_dm = demucs_pct_pattern.match(clean)
                    if m_dl or m_dm:
                        pct = int(float((m_dl or m_dm).group(1)))
                        self.progress['value'] = pct
                        self.status_var.set(last_label)
                        msg = f"[DEBUG] Progress update: {pct}%, label: '{last_label}'"
                        self.after(0, self._append_log, msg)
                    else:
                        # fallback: any percentage
                        m_gen = generic_pct_pattern.search(clean)
                        if m_gen:
                            pct = int(float(m_gen.group(1)))
                            self.progress['value'] = pct
                            self.status_var.set('Working...')
                            msg =  f"[DEBUG] Fallback progress: {pct}% (Working...)"
                            self.after(0, self._append_log, msg)

        proc.wait()
        self.after(0, self._reset_ui, proc.returncode == 0)

    def _reset_ui(self, success):
        self.convert_btn.config(state='normal', text='Convert')
        self.progress['value'] = 100 if success else 0
        self.status_var.set('Done' if success else 'Ready')
        self.src.set('')

        if success:
            self.after(0, messagebox.showinfo, 'Done', 'Conversion finished!')
            output_dir = os.path.join(os.getcwd(), 'songs', 'output')
            try:
                if sys.platform.startswith('win'):
                    os.startfile(output_dir)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', output_dir], check=True)
                else:
                    subprocess.run(['xdg-open', output_dir], check=True)
            except Exception as e:
                self.after(0, messagebox.showwarning,
                           'Could not open folder', str(e))

if __name__ == '__main__':
    ConverterApp().mainloop()
