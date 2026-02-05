import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import locale
import ctypes
import sys

# --- FUNKCE PRO CESTY K SOUBORŮM V EXE ---
def resource_path(relative_path):
    """ Získá cestu k souboru, funguje pro vývoj i pro PyInstaller .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- PŘEKLADY ---
TRANSLATIONS = {
    'cs': {
        'title': 'ME7 Logger Patcher (5120 Hack)',
        'heading': 'ME7 Logger Patcher (5120 Hack)',
        'subheading': 'Násobení hodnot 2x pro korektní zobrazení tlaku',
        'frame_title': ' Vyberte kanály k přepočtu ',
        'btn_start': 'VYBRAT LOG A PŘEPOČÍTAT',
        'ready': 'Připraven k úpravě...',
        'no_selection': 'Musíte vybrat alespoň jednu proměnnou k násobení!',
        'no_vars_found': 'V logu nebyla nalezena žádná ze zvolených proměnných!',
        'success': 'Log byl upraven a uložen.',
        'error': 'Došlo k chybě:',
        'lang_label': 'Jazyk:',
        'plsol_w': '{BoostPressureDesired}',
        'ps_w': '{ModelledIntakeManifoldPressure}',
        'pssol_w': '{DesiredIntakeManifoldPressure}',
        'pu_w': '{BaroPressure}',
        'pvdkds_w': '{BoostPressureActual}',
        'custom_label': 'Vlastní kanál (volitelné):'
    },
    'en': {
        'title': 'ME7 Logger Patcher (5120 Hack)',
        'heading': 'ME7 Logger Patcher (5120 Hack)',
        'subheading': 'Multiply values by 2x for correct pressure display',
        'frame_title': ' Select channels to convert ',
        'btn_start': 'SELECT LOG AND CALCULATE',
        'ready': 'Ready for patching...',
        'no_selection': 'You must select at least one variable to multiply!',
        'no_vars_found': 'No selected variables found in the log!',
        'success': 'Log has been patched and saved.',
        'error': 'An error occurred:',
        'lang_label': 'Language:',
        'plsol_w': '{BoostPressureDesired}',
        'ps_w': '{ModelledIntakeManifoldPressure}',
        'pssol_w': '{DesiredIntakeManifoldPressure}',
        'pu_w': '{BaroPressure}',
        'pvdkds_w': '{BoostPressureActual}',
        'custom_label': 'Custom channel (optional):'
    }
}

# --- LOGIKA VÝPOČTU ---
def process_me7_log():
    lang = current_lang.get()
    
    # 1. Standardní vybrané kanály
    selected_vars = [var for var, state in checkboxes.items() if state.get()]
    
    # 2. Přidání vlastního kanálu
    custom_v = custom_var_entry.get().strip()
    if custom_v:
        selected_vars.append(custom_v)
    
    if not selected_vars:
        messagebox.showwarning("!", TRANSLATIONS[lang]['no_selection'])
        return

    input_path = filedialog.askopenfilename(
        title="Select ME7 Log",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not input_path: return

    try:
        with open(input_path, 'r', encoding='cp1250', errors='ignore') as f:
            lines = f.readlines()

        output_lines = []
        header_index = -1
        col_indices = {}

        # Vyhledání indexů sloupců
        for i, line in enumerate(lines):
            if 'TimeStamp' in line:
                header_index = i
                columns = [c.strip() for c in line.split(',')]
                for target in selected_vars:
                    if target in columns:
                        col_indices[target] = columns.index(target)
                break
        
        if not col_indices:
            messagebox.showwarning("!", TRANSLATIONS[lang]['no_vars_found'])
            return

        # Zpracování dat (data začínají obvykle 3 řádky pod hlavičkou v ME7 logu)
        data_start_index = header_index + 3
        for i, line in enumerate(lines):
            if i >= data_start_index and line.strip():
                parts = line.split(',')
                for col_name, idx in col_indices.items():
                    if idx < len(parts):
                        try:
                            raw_val = parts[idx].strip()
                            if raw_val:
                                val = float(raw_val)
                                parts[idx] = f" {val * 2:.2f} "
                        except ValueError:
                            pass 
                output_lines.append(','.join(parts))
            else:
                output_lines.append(line)

        # Uložení souboru
        folder = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_path = os.path.join(folder, f"{name}-doubled-{ext}")

        with open(output_path, 'w', encoding='cp1250') as f:
            f.writelines(output_lines)

        status_label.config(text=f"✅ {name}-doubled-{ext}", fg="#28a745")
        messagebox.showinfo("OK", TRANSLATIONS[lang]['success'])

    except Exception as e:
        status_label.config(text="❌ Error", fg="#dc3545")
        messagebox.showerror("Error", f"{TRANSLATIONS[lang]['error']} {e}")

# --- PŘEPÍNÁNÍ JAZYKA ---
def change_language(*args):
    lang = current_lang.get()
    root.title(TRANSLATIONS[lang]['title'])
    heading_label.config(text=TRANSLATIONS[lang]['heading'])
    subheading_label.config(text=TRANSLATIONS[lang]['subheading'])
    checkbox_frame.config(text=TRANSLATIONS[lang]['frame_title'])
    btn.config(text=TRANSLATIONS[lang]['btn_start'])
    status_label.config(text=TRANSLATIONS[lang]['ready'])
    lang_info_label.config(text=TRANSLATIONS[lang]['lang_label'])
    custom_label.config(text=TRANSLATIONS[lang]['custom_label'])
    
    for var, cb_obj in checkbox_widgets.items():
        display_text = f"{var.ljust(10)} | {TRANSLATIONS[lang][var]}"
        cb_obj.config(text=display_text)

# --- GUI SETUP ---
root = tk.Tk()
root.geometry("580x620")
root.configure(padx=25, pady=20)

# Ikona a Taskbar fix
icon_name = "favicon.ico"
icon_path = resource_path(icon_name)
if os.path.exists(icon_path):
    try:
        root.iconbitmap(icon_path)
        myappid = 'alesv.tuning.me7patcher.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass

# Detekce jazyka
try:
    sys_lang = locale.getlocale()[0]
except:
    sys_lang = None
default_lang = 'cs' if sys_lang and ('cs' in sys_lang.lower() or 'czech' in sys_lang.lower()) else 'en'
current_lang = tk.StringVar(value=default_lang)

# Horní lišta s jazykem
lang_frame = tk.Frame(root)
lang_frame.pack(anchor="ne")
lang_info_label = tk.Label(lang_frame, text="", font=("Arial", 8))
lang_info_label.pack(side="left")
lang_combo = ttk.Combobox(lang_frame, textvariable=current_lang, values=['cs', 'en'], width=5, state="readonly")
lang_combo.pack(side="left", padx=5)
current_lang.trace_add("write", change_language)

# Nadpisy
heading_label = tk.Label(root, text="", font=("Arial", 14, "bold"), fg="#d9534f")
heading_label.pack(pady=(10, 5))
subheading_label = tk.Label(root, text="", font=("Arial", 10, "italic"))
subheading_label.pack(pady=(0, 15))

# Sekce s checkboxy
checkbox_frame = tk.LabelFrame(root, text="", padx=15, pady=15)
checkbox_frame.pack(fill="x", pady=10)

checkboxes = {}
checkbox_widgets = {}
TARGET_CHANNELS = ['plsol_w', 'ps_w', 'pssol_w', 'pu_w', 'pvdkds_w']

for var in TARGET_CHANNELS:
    var_state = tk.BooleanVar(value=True)
    cb = tk.Checkbutton(checkbox_frame, text="", variable=var_state, anchor="w", font=("Courier", 9))
    cb.pack(fill="x")
    checkboxes[var] = var_state
    checkbox_widgets[var] = cb

# Vlastní kanál
custom_frame = tk.Frame(root)
custom_frame.pack(fill="x", pady=5)
custom_label = tk.Label(custom_frame, text="", font=("Arial", 9))
custom_label.pack(side="left")
custom_var_entry = tk.Entry(custom_frame, font=("Courier", 10), width=15)
custom_var_entry.pack(side="left", padx=10)

# Hlavní tlačítko
btn = tk.Button(root, text="", command=process_me7_log, 
               bg="#d9534f", fg="white", font=("Arial", 10, "bold"), 
               padx=20, pady=12, cursor="hand2")
btn.pack(pady=20)

status_label = tk.Label(root, text="", font=("Arial", 9, "italic"))
status_label.pack()

# Kredity
about_frame = tk.Frame(root)
about_frame.pack(side="bottom", pady=(20, 0))
tk.Label(about_frame, text="Powered by Gemini AI (Google)", font=("Arial", 10), fg="#5dade2").pack()
tk.Label(about_frame, text="Created by Aleš Veigend", font=("Arial", 11, "bold")).pack()
tk.Label(about_frame, text="AlesVeigend@hotmail.cz", font=("Arial", 10)).pack()
tk.Label(about_frame, text="Version 1.0 | 2026", font=("Arial", 10), fg="gray").pack()

# Inicializace
change_language()
root.mainloop()
