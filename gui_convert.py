import os
import subprocess
import sys
import threading
import re
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

ULTRAS_FLAGS = {
    'interactive': None,
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
        self.resizable(False, False)

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
        self.frame = ttk.Frame(self)
        self.vars, self.widgets = {}, {}
        r=0
        for f, opts in ULTRAS_FLAGS.items():
            v = tk.BooleanVar()
            chk = ttk.Checkbutton(self.frame, text=f, variable=v, command=lambda f=f: self.toggle_flag(f))
            chk.grid(column=0, row=r, sticky='w', padx=5)
            self.vars[f] = v
            if opts:
                dd = ttk.Combobox(self.frame, values=opts, state='disabled')
                dd.grid(column=1, row=r, padx=5)
                self.widgets[f] = dd
            r += 1

        self.convert_btn = ttk.Button(self, text='Convert', command=self.start_conversion)
        self.convert_btn.grid(column=0, row=99, padx=10, pady=10)

    def toggle(self):
        if not self.adv:
            self.frame.grid(column=0, row=5, padx=10)
            self.adv_btn.config(text='Hide Advanced')
        else:
            self.frame.grid_forget()
            self.adv_btn.config(text='Show Advanced')
        self.adv = not self.adv

    def toggle_flag(self, flag):
        w = self.widgets.get(flag)
        if self.vars[flag].get() and w:
            w.config(state='readonly')
            w.set(ULTRAS_FLAGS[flag][0])
        elif w:
            w.config(state='disabled')

    def check_docker(self):
        try:
            subprocess.check_output(['docker','--version'])
            subprocess.check_output(['docker','compose','version'])
            return True
        except Exception:
            return False

    def install_docker(self):
        inst = os.path.join(os.getcwd(),'DockerDesktopInstaller.exe')
        if not os.path.exists(inst):
            url = 'https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe'
            subprocess.run(['powershell','-Command',f"iwr -Uri {url} -OutFile {inst}"], check=True)
        subprocess.run([inst,'install','--quiet'], check=True)

    def start_conversion(self):
        # disable button and update text
        self.convert_btn.config(state='disabled', text='Processing...')
        self.progress['value'] = 0
        threading.Thread(target=self.convert, daemon=True).start()

    def convert(self):
        self.status_var.set('Initializing...')
        src = self.src.get().strip()
        if not src:
            messagebox.showerror('Error','Enter valid input')
            self._reset_ui()
            return

        # Normalize YouTube URL: keep only 'v' param
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
            except Exception:
                pass

        # Docker check/install
        self.status_var.set('Checking Docker...')
        if not self.check_docker():
            if messagebox.askyesno('Install?','Docker not found. Install?'):
                self.status_var.set('Installing Docker...')
                self.install_docker()
            else:
                self._reset_ui()
                return

        # Gather flags
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
        self.status_var.set('Starting container...')
        subprocess.run(['docker','compose','-f','compose-nogpu.yml','up','-d','--force-recreate'], cwd=songs, check=True)

        # Install MuseScore
        self.status_var.set('Installing MuseScore...')
        subprocess.run([
            'docker','exec','-u','root','UltraSinger','bash','-lc',
            "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y musescore3 && apt-get clean"
        ], cwd=songs, check=True)

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
        for line in proc.stdout:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
            print(clean, end='')
            line = re.sub(r"\x1b\[[0-9;]*m", "", line) #clean line from color codes
            m = re.match(r".*\[UltraSinger\]\s*(.*)", clean)
            if m:
                last_label = m.group(1).strip() or "Working"
                print(f"[DEBUG] Label set to: '{last_label}'")
            # update on item downloads
            m_item = item_pattern.search(line)
            if m_item:
                cur, tot = map(int, m_item.groups())
                pct = int(cur / tot * 100)
                self.progress['value'] = pct
                self.status_var.set(f"Downloading item {cur} of {tot}")
                print(f"[DEBUG] Item download: {pct}%")
            else:
                # slash-based counts (e.g. 1/552)
                m_slash = slash_pct_pattern.match(line)
                if m_slash:
                    cur, tot = map(int, m_slash.groups())
                    pct = int(cur / tot * 100)
                    self.progress['value'] = pct
                    self.status_var.set(last_label)
                    print(f"[DEBUG] Slash progress: {pct}%, label: '{last_label}'")
                else:
                    # youtube-dl download percentages or demucs
                    m_dl = download_pct_pattern.match(line)
                    m_dm = demucs_pct_pattern.match(line)
                    if m_dl or m_dm:
                        pct = int(float((m_dl or m_dm).group(1)))
                        self.progress['value'] = pct
                        self.status_var.set(last_label)
                        print(f"[DEBUG] Progress update: {pct}%, label: '{last_label}'")
                    else:
                        # fallback: any percentage
                        m_gen = generic_pct_pattern.search(line)
                        if m_gen:
                            pct = int(float(m_gen.group(1)))
                            self.progress['value'] = pct
                            self.status_var.set('Working...')
                            print(f"[DEBUG] Fallback progress: {pct}% (Working...)")
        proc.wait()

        self._reset_ui(success=(proc.returncode==0))

    def _reset_ui(self, success=False):
        # restore button
        self.convert_btn.config(state='normal', text='Convert')
        self.progress['value'] = 100 if success else 0
        self.status_var.set('Done' if success else 'Ready')
        if success:
            messagebox.showinfo('Done','Check songs/output')

if __name__=='__main__':
    ConverterApp().mainloop()
