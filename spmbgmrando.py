import os
import platform
import random
import re
import shutil
import struct
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

selected_folder = ""
file_checkbox_vars = {}


def select_sound_folder():
    global selected_folder
    folder_selected = filedialog.askdirectory(title="Select Sound Folder")

    if not folder_selected:
        return

    selected_folder = folder_selected
    if os.path.basename(folder_selected).lower() != "sound":
        messagebox.showerror(
            "Invalid Folder", "Please select a folder named 'sound'."
        )
        return

    brstm_files = [
        f
        for f in os.listdir(folder_selected)
        if f.lower().endswith(".brstm")
        and os.path.isfile(os.path.join(folder_selected, f))
    ]

    if not brstm_files:
        messagebox.showerror(
            "No BRSTM Files",
            "No .brstm files were found in the selected folder.",
        )
        return

    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    file_checkbox_vars.clear()

    for file in brstm_files:
        var = tk.BooleanVar(value=True)
        file_checkbox_vars[file] = var

        cb = tk.Checkbutton(
            scrollable_frame,
            text=file,
            variable=var,
            anchor="w",
            justify="left",
            activebackground="#e1f0ff",
        )
        cb.pack(fill=tk.X, expand=True, padx=2, pady=1)

        cb.bind("<Double-Button-1>", open_selected_file)
        cb.bind("<Enter>", on_enter)
        cb.bind("<Leave>", on_leave)

    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


def open_selected_file(event):
    widget = event.widget
    filename = widget.cget("text")

    if filename and selected_folder:
        full_path = os.path.join(selected_folder, filename)
        temp_dir = tempfile.gettempdir()
        temp_wav = os.path.join(temp_dir, filename.replace(".brstm", ".wav"))

        try:
            system_os = platform.system()
            vgaudio_dir = os.path.join(os.path.dirname(__file__), "VGAudio")

            if system_os == "Windows":
                vgaudio_bin = os.path.join(vgaudio_dir, "VGAudioCli.exe")
                cmd = [vgaudio_bin, full_path, temp_wav]
            else:
                vgaudio_bin = os.path.join(vgaudio_dir, "VGAudioCli.dll")
                cmd = ["dotnet", vgaudio_bin, full_path, temp_wav]

            subprocess.run(cmd, check=True)

            if system_os == "Windows":
                os.startfile(temp_wav)
            elif system_os == "Darwin":
                subprocess.run(["open", temp_wav])
            else:
                subprocess.run(["xdg-open", temp_wav])

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to play preview.\n\nDetails: {e}"
            )


def on_enter(event):
    event.widget.config(bg="#e1f0ff")


def on_leave(event):
    event.widget.config(bg="SystemButtonFace")


def backup_sound():
    if not selected_folder:
        return messagebox.showerror(
            "Error", "You have to select the sound folder first."
        )

    brstm_files = [
        f for f in os.listdir(selected_folder) if f.lower().endswith(".brstm")
    ]

    if not brstm_files:
        return messagebox.showwarning(
            "Warning", "No .brstm files found to backup."
        )

    backup_dir = os.path.join(os.getcwd(), "Sound_backup")
    os.makedirs(backup_dir, exist_ok=True)

    prog_win, status_label, prog_bar = backup_progress_window(root)
    prog_bar["maximum"] = len(brstm_files)
    current_step = 0

    try:
        for filename in brstm_files:
            status_label.config(text=f"Backing up: {filename}")
            src_path = os.path.join(selected_folder, filename)
            dest_path = os.path.join(backup_dir, filename)

            shutil.copy2(src_path, dest_path)

            current_step += 1
            prog_bar["value"] = current_step
            prog_win.update()

        prog_win.destroy()
        messagebox.showinfo(
            "Backup Complete", "Backup folder created successfully!"
        )

    except Exception as e:
        prog_win.destroy()
        messagebox.showerror(
            "Backup Error", f"An error occurred during backup:\n\n{e}"
        )


def load_backup_folder():
    if not selected_folder:
        return messagebox.showerror(
            "Error", "You have to select the sound folder first."
        )

    replace_dir = os.path.join(os.getcwd(), "Sound_backup")

    if not os.path.exists(replace_dir):
        user_choice = messagebox.askyesno(
            "Can't Find Backup Folder",
            "You have to make a backup first. Create one now?",
        )
        if user_choice:
            return backup_sound()
        return

    brstm_files = [
        f for f in os.listdir(replace_dir) if f.lower().endswith(".brstm")
    ]

    if not brstm_files:
        return messagebox.showwarning(
            "Warning", "No .brstm files found in the Sound_backup folder."
        )

    prog_win, status_label, prog_bar = create_progress_window(
        root, title="Restoring Backup..."
    )
    prog_bar["maximum"] = len(brstm_files)
    current_step = 0

    try:
        for filename in brstm_files:
            status_label.config(text=f"Restoring: {filename}")
            src_path = os.path.join(replace_dir, filename)
            dest_path = os.path.join(selected_folder, filename)

            shutil.copy2(src_path, dest_path)

            current_step += 1
            prog_bar["value"] = current_step
            prog_win.update()

        prog_win.destroy()
        messagebox.showinfo(
            "Restore Complete", "Successfully restored files from backup!"
        )

    except Exception as e:
        prog_win.destroy()
        messagebox.showerror(
            "Restore Error", f"An error occurred while restoring backup:\n\n{e}"
        )


def getwitpath():
    system_os = platform.system()
    wit_dir = os.path.join(os.path.dirname(__file__), "wit")

    if system_os == "Windows":
        return os.path.join(wit_dir, "wit.exe")
    elif system_os == "Darwin":
        return os.path.join(wit_dir, "wit_mac")
    else:
        return os.path.join(wit_dir, "wit_linux")


def extract_iso():
    iso_path = filedialog.askopenfilename(
        title="Select ISO File",
        filetypes=[
            ("ISO Files", "*.iso"),
            ("WBFS Files", "*.wbfs"),
            ("All files", "*.*"),
        ],
    )

    if not iso_path:
        return

    spm_game_ids = {"R8PE01", "R8PP01", "R8PJ01", "R8PK01"}
    wit_bin = getwitpath()

    try:
        raw_id = subprocess.check_output(
            [wit_bin, "id", iso_path],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()

        game_id = raw_id[:6].upper()

        if game_id not in spm_game_ids:
            return messagebox.showerror(
                "Invalid file",
                "Selected file is not Super Paper Mario",
            )
    except Exception as e:
        return messagebox.showerror(
            "Error",
            f"Failed to get game ID:\n{e}",
        )

    filetype = "file"
    if iso_path.lower().endswith(".iso"):
        filetype = "ISO"
    elif iso_path.lower().endswith(".wbfs"):
        filetype = "WBFS"

    base_dir = filedialog.askdirectory(title="Select Extraction Folder")
    if not base_dir:
        return

    output_dir = os.path.join(base_dir, game_id)

    prog_win, status_label, prog_bar = create_progress_window(
        root, title=f"Extracting {filetype}..."
    )
    prog_bar["maximum"] = 100
    prog_bar["value"] = 0
    status_label.config(text="Starting WIT extraction...")
    prog_win.update()

    try:
        cmd = [wit_bin, "extract", iso_path, output_dir, "--progress"]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        percent_pattern = re.compile(r"(\d+)%")

        for line in iter(process.stdout.readline, ""):
            match = percent_pattern.search(line)
            if match:
                percent_val = int(match.group(1))
                prog_bar["value"] = percent_val
                status_label.config(
                    text=f"Extracting {filetype}... {percent_val}%"
                )
                prog_win.update()

        process.stdout.close()
        return_code = process.wait()

        prog_win.destroy()

        if return_code == 0:
            messagebox.showinfo(
                "Extraction Complete",
                f"Successfully extracted {filetype} to:\n{output_dir}",
            )
        else:
            messagebox.showerror(
                "Error",
                f"WIT exited with error code {return_code}.",
            )

    except Exception as e:
        prog_win.destroy()
        messagebox.showerror(
            "Error",
            f"Could not extract {filetype}.\n\nDetails: {e}",
        )


def rebuild_iso():
    iso_folder = filedialog.askdirectory(
        title="Select SPM Folder",
    )

    if not iso_folder:
        return

    target_dir = None
    if os.path.exists(os.path.join(iso_folder, "sys")) and os.path.exists(
        os.path.join(iso_folder, "files")
    ):
        target_dir = iso_folder
    else:
        for root_path, dirs, _ in os.walk(iso_folder):
            if "sys" in dirs and "files" in dirs:
                target_dir = root_path
                break

    if not target_dir:
        messagebox.showerror(
            "Invalid Folder Structure",
            "Could not locate 'sys' and 'files' folders in the selected folder.",
        )
        return

    base_dir = filedialog.asksaveasfilename(
        title="Save Rebuilt File As",
        defaultextension=".iso",
        filetypes=[
            ("ISO file", "*.iso"),
            ("WBFS file", "*.wbfs"),
            ("All files", "*.*"),
        ],
    )
    if not base_dir:
        return

    output_dir = base_dir

    prog_win, status_label, prog_bar = create_progress_window(
        root, title="Rebuilding ISO..."
    )
    prog_bar["maximum"] = 100
    prog_bar["value"] = 0
    status_label.config(text="Starting WIT rebuild...")
    prog_win.update()

    filetype = "file"
    if output_dir.lower().endswith(".iso"):
        filetype = "ISO"
    elif output_dir.lower().endswith(".wbfs"):
        filetype = "WBFS"

    try:
        wit_bin = getwitpath()
        cmd = [
            wit_bin,
            "copy",
            "--align-files",
            target_dir,
            output_dir,
            "--progress",
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        percent_pattern = re.compile(r"(\d+)%")

        for line in iter(process.stdout.readline, ""):
            match = percent_pattern.search(line)
            if match:
                percent_val = int(match.group(1))
                prog_bar["value"] = percent_val
                status_label.config(
                    text=f"Rebuilding {filetype}... {percent_val}%"
                )
                prog_win.update()

        process.stdout.close()
        return_code = process.wait()

        prog_win.destroy()

        if return_code == 0:
            messagebox.showinfo(
                "Rebuild Complete",
                f"Successfully rebuilt {filetype} to:\n{output_dir}",
            )
        else:
            messagebox.showerror(
                "Error",
                f"WIT exited with error code {return_code}.",
            )

    except Exception as e:
        prog_win.destroy()
        messagebox.showerror(
            "Error",
            f"Could not rebuild {filetype}.\n\nDetails: {e}",
        )


def create_progress_window(parent, title="Randomizing Brstm..."):
    progress_win = tk.Toplevel(parent)
    progress_win.title(title)
    progress_win.geometry("350x120")
    progress_win.resizable(False, False)
    progress_win.transient(parent)
    progress_win.grab_set()

    progress_win.grab_set()
    try:
        progress_win.iconbitmap("app_icon.ico")
    except Exception:
        pass
    status_label = tk.Label(
        progress_win, text="Preparing...", font=("Arial", 10)
    )
    status_label.pack(pady=(15, 5))

    progress_bar = ttk.Progressbar(
        progress_win, orient="horizontal", length=280, mode="determinate"
    )
    progress_bar.pack(pady=10)

    progress_win.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (350 // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (120 // 2)
    progress_win.geometry(f"+{x}+{y}")

    return progress_win, status_label, progress_bar


def backup_progress_window(parent, title="Creating backup..."):
    progress_win = tk.Toplevel(parent)
    progress_win.title(title)
    progress_win.geometry("350x120")
    progress_win.resizable(False, False)
    progress_win.transient(parent)
    progress_win.grab_set()
    try:
        progress_win.iconbitmap("app_icon.ico")
    except Exception:
        pass
    status_label = tk.Label(
        progress_win, text="Creating backup...", font=("Arial", 10)
    )
    status_label.pack(pady=(15, 5))

    progress_bar = ttk.Progressbar(
        progress_win, orient="horizontal", length=280, mode="determinate"
    )
    progress_bar.pack(pady=10)

    progress_win.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (350 // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (120 // 2)
    progress_win.geometry(f"+{x}+{y}")

    return progress_win, status_label, progress_bar


root = tk.Tk()
root.title("SpmBgmRando")
root.geometry("700x450")
root.resizable(False, False)
try:
    root.iconbitmap("app_icon.ico")
except Exception:
    pass

menu_bar = tk.Menu(root)
allow_duplicates = tk.BooleanVar(value=False)
categorised = tk.BooleanVar(value=False)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Select sound folder", command=select_sound_folder)
file_menu.add_command(label="Extract Iso/Wbfs file", command=extract_iso)
file_menu.add_command(label="Rebuild Iso/Wbfs file", command=rebuild_iso)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

tools_menu = tk.Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Create backup folder", command=backup_sound)
tools_menu.add_command(label="Load backup folder", command=load_backup_folder)
menu_bar.add_cascade(label="Options", menu=tools_menu)

help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(
    label="About",
    command=lambda: messagebox.showinfo(
        "About SpmBgmRando",
        "Super Paper Mario BGM Randomizer v1.2\n"
        "Created by FleepFan\n"
        "Powered by Wiimms ISO Tools (WIT) and VGAudio",
    ),
)
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

main_frame = tk.Frame(root)

left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

canvas = tk.Canvas(left_frame, highlightthickness=0)
scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
)

canvas_window = canvas.create_window(
    (0, 0), window=scrollable_frame, anchor="nw"
)

canvas.bind(
    "<Configure>",
    lambda e: canvas.itemconfig(canvas_window, width=e.width),
)

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def select_all_files():
    for var in file_checkbox_vars.values():
        var.set(True)


def deselect_all_files():
    for var in file_checkbox_vars.values():
        var.set(False)


def deselect_shorts():
    target_files = {
        "b_happy_flower_44k_lp.brstm",
        "evt_hamerustone1_44k_lp.brstm",
        "evt_happy_flower_44k.brstm",
        "evt_opn_paper1_32k.brstm",
        "evt_op_book_s_lp.brstm",
        "evt_staff1_44k_lp.brstm",
        "evt_stg6_syoumetsu1_e1.brstm",
        "evt_stg7_rpg_ff1_e2_44k.brstm",
        "ff_areastart_44k_lp.brstm",
        "ff_card_get1_lp.brstm",
        "ff_companion1_44k_lp.brstm",
        "ff_correct1_32k.brstm",
        "ff_corrrect2_e3_32k.brstm",
        "ff_failinget1_32k.brstm",
        "ff_fault1_32k.brstm",
        "ff_itemget1_32k.brstm",
        "ff_itemget2_32k.brstm",
        "ff_levelup1_32k.brstm",
        "ff_pureheart_get_s2_lp.brstm",
        "ff_umai1_e1_lp.brstm",
        "ff_yado1_44k_lp.brstm",
        "ff_zigenwaza_get1_44k_lp.brstm",
        "map_stg1_start1_44k_lp.brstm",
        "map_stg2_start1_44k_lp.brstm",
        "map_stg3_start1_44k_lp.brstm",
        "map_stg4_start1_44k_lp.brstm",
        "map_stg5_start1_44k_lp.brstm",
        "map_stg6_start1_44k_lp.brstm",
        "map_stg7_start1_44k_lp.brstm",
        "map_stg8_start1_44k_lp.brstm",
        "sys_gameover1_44k_lp.brstm",
        "sys_stage_clear_E3_lp.brstm",
        "sys_yarare1_44k_lp.brstm",
    }

    for filename, var in file_checkbox_vars.items():
        if filename in target_files:
            var.set(False)


def select_shorts():
    target_files = {
        "b_happy_flower_44k_lp.brstm",
        "evt_hamerustone1_44k_lp.brstm",
        "evt_happy_flower_44k.brstm",
        "evt_opn_paper1_32k.brstm",
        "evt_op_book_s_lp.brstm",
        "evt_staff1_44k_lp.brstm",
        "evt_stg6_syoumetsu1_e1.brstm",
        "evt_stg7_rpg_ff1_e2_44k.brstm",
        "ff_areastart_44k_lp.brstm",
        "ff_card_get1_lp.brstm",
        "ff_companion1_44k_lp.brstm",
        "ff_correct1_32k.brstm",
        "ff_corrrect2_e3_32k.brstm",
        "ff_failinget1_32k.brstm",
        "ff_fault1_32k.brstm",
        "ff_itemget1_32k.brstm",
        "ff_itemget2_32k.brstm",
        "ff_levelup1_32k.brstm",
        "ff_pureheart_get_s2_lp.brstm",
        "ff_umai1_e1_lp.brstm",
        "ff_yado1_44k_lp.brstm",
        "ff_zigenwaza_get1_44k_lp.brstm",
        "map_stg1_start1_44k_lp.brstm",
        "map_stg2_start1_44k_lp.brstm",
        "map_stg3_start1_44k_lp.brstm",
        "map_stg4_start1_44k_lp.brstm",
        "map_stg5_start1_44k_lp.brstm",
        "map_stg6_start1_44k_lp.brstm",
        "map_stg7_start1_44k_lp.brstm",
        "map_stg8_start1_44k_lp.brstm",
        "sys_gameover1_44k_lp.brstm",
        "sys_stage_clear_E3_lp.brstm",
        "sys_yarare1_44k_lp.brstm",
    }

    for filename, var in file_checkbox_vars.items():
        if filename in target_files:
            var.set(True)


def deselect_unused():
    target_files = {
        "b_happy_flower_44k_lp.brstm",
        "evt_relax1_44k_lp.brstm",
        "evt_stg3_open_44k_lp.brstm",
        "evt_happy_flower_44k.brstm",
        "dummy_32k.brstm",
    }

    for filename, var in file_checkbox_vars.items():
        if filename in target_files:
            var.set(False)


def select_unused():
    target_files = {
        "b_happy_flower_44k_lp.brstm",
        "evt_relax1_44k_lp.brstm",
        "evt_stg3_open_44k_lp.brstm",
        "evt_happy_flower_44k.brstm",
        "dummy_32k.brstm",
    }

    for filename, var in file_checkbox_vars.items():
        if filename in target_files:
            var.set(True)


canvas.bind_all("<MouseWheel>", _on_mousewheel)

divider = tk.Frame(main_frame, width=2, bg="#cccccc")
divider.pack(side=tk.LEFT, fill=tk.Y, padx=10)

right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

options_label = tk.Label(
    right_frame, text="Randomizer Options", font=("Arial", 12, "bold")
)
options_label.pack(anchor="nw", pady=(0, 10))

select_frame = tk.Frame(right_frame)
select_frame.pack(anchor="nw", fill=tk.X, pady=(0, 15))


def add_option_button(
    parent_frame, text, command_function, side=tk.TOP, padx=0, pady=0
):
    btn = tk.Button(
        parent_frame,
        text=text,
        command=command_function,
        anchor="w",
        padx=10,
        pady=5,
    )
    btn.pack(fill=tk.X, pady=2)
    return btn


btn_select_all = add_option_button(
    select_frame, "Select All", select_all_files, side=tk.LEFT, padx=(0, 5)
)

btn_deselect_all = add_option_button(
    select_frame, "Deselect All", deselect_all_files, side=tk.LEFT
)
btn_deselect_shorts = add_option_button(
    select_frame, "Deselect Shorts", deselect_shorts, side=tk.LEFT
)
btn_select_shorts = add_option_button(
    select_frame, "Select Shorts", select_shorts, side=tk.LEFT
)
btn_deselect_unused = add_option_button(
    select_frame, "Deselect Unused", deselect_unused, side=tk.LEFT
)
btn_select_unused = add_option_button(
    select_frame, "Select Unused", select_unused, side=tk.LEFT
)


def show_info(title, text):
    messagebox.showinfo(title, text)


def limit_entry_length(P, max_length=15):
    return (P == "" or P.isdigit()) and len(P) <= max_length


seed_frame = tk.Frame(right_frame)
seed_frame.pack(anchor="nw", fill=tk.X, pady=(0, 5))

seed_label = tk.Label(seed_frame, text="Seed:", font=("Arial", 11, "bold"))
seed_label.pack(side=tk.LEFT, padx=(0, 5))

val_cmd = root.register(lambda P: limit_entry_length(P, max_length=10))

seed_entry = tk.Entry(
    seed_frame,
    bg="white",
    fg="black",
    width=10,
    validate="key",
    validatecommand=(val_cmd, "%P"),
)
seed_entry.pack(side=tk.LEFT)

row1 = tk.Frame(right_frame)
row1.pack(fill="x", pady=2, anchor="w")

chk_dup = tk.Checkbutton(
    row1, text="Allow Duplicates", variable=allow_duplicates
)
chk_dup.pack(side="left")

btn_info1 = tk.Button(
    row1,
    text="[i]",
    font=("Arial", 8, "bold"),
    fg="blue",
    relief="flat",
    cursor="hand2",
    command=lambda: show_info(
        "Allow Duplicates",
        "Allows a single track to be assigned to multiple original sound files.",
    ),
)
btn_info1.pack(side="left", padx=5)

row2 = tk.Frame(right_frame)
row2.pack(fill="x", pady=2, anchor="w")

chk_cat = tk.Checkbutton(row2, text="Categorize", variable=categorised)
chk_cat.pack(side="left")

btn_info2 = tk.Button(
    row2,
    text="[i]",
    font=("Arial", 8, "bold"),
    fg="blue",
    relief="flat",
    cursor="hand2",
    command=lambda: show_info(
        "Categorize",
        "Only shuffles tracks within the same prefix group (e.g., map_ with map_, btl_ with btl_, evt_ with evt_).",
    ),
)
btn_info2.pack(side="left", padx=5)


def randomize_music():
    if not selected_folder:
        messagebox.showwarning("Warning", "Please select a sound folder first.")
        return

    if not os.path.exists(os.path.join(os.getcwd(), "Sound_backup")):
        _proceed = messagebox.askyesno(
            "Backup recommended",
            "Backup folder was not found, proceed anyway?",
        )
        if not _proceed:
            createnow = messagebox.askyesno(
                "Create backup",
                "Create backup folder now?",
            )
            if createnow:
                return backup_sound()
            else:
                return

    selected_filenames = [
        filename for filename, var in file_checkbox_vars.items() if var.get()
    ]

    if len(selected_filenames) < 2:
        messagebox.showwarning(
            "Warning", "Please select at least 2 files to randomize."
        )
        return

    should_loop_unlooped = messagebox.askyesno(
        "loop selection",
        "do you want to loop every brstm?",
    )
    if should_loop_unlooped:
        replace_dir = os.path.join(os.getcwd(), "replace")

        if not os.path.exists(replace_dir):
            user_choice = messagebox.askyesno(
                "Can't Find Replace Folder",
                "Can't find the 'replace' folder. Continue without pre-looped files?",
            )
            if not user_choice:
                return
        else:
            for filename in os.listdir(replace_dir):
                if filename.lower().endswith(".brstm"):
                    src_path = os.path.join(replace_dir, filename)
                    dest_path = os.path.join(selected_folder, filename)
                    shutil.copy2(src_path, dest_path)

    user_seed = seed_entry.get().strip()
    if user_seed:
        current_seed = user_seed
    else:
        current_seed = str(random.randint(0, 9999999999))
    random.seed(current_seed)

    if categorised.get():
        from collections import defaultdict

        categories = defaultdict(list)
        for filename in selected_filenames:
            if "_" in filename:
                prefix = filename.split("_")[0]
            else:
                prefix = "other"
            categories[prefix].append(filename)

        assigned_dict = {}

        for prefix, group_files in categories.items():
            if allow_duplicates.get():
                group_assigned = [
                    random.choice(group_files) for _ in group_files
                ]
            else:
                group_assigned = group_files.copy()
                random.shuffle(group_assigned)

            for target_file, source_file in zip(group_files, group_assigned):
                assigned_dict[target_file] = source_file

        assigned_sources = [assigned_dict[name] for name in selected_filenames]
    else:
        if allow_duplicates.get():
            assigned_sources = [
                random.choice(selected_filenames) for _ in selected_filenames
            ]
        else:
            assigned_sources = selected_filenames.copy()
            random.shuffle(assigned_sources)

    unique_sources = list(set(assigned_sources))
    total_steps = len(unique_sources) + len(selected_filenames)

    prog_win, status_label, prog_bar = create_progress_window(root)
    prog_bar["maximum"] = total_steps
    current_step = 0

    try:
        temp_dir = tempfile.mkdtemp()

        for original_name in unique_sources:
            src_path = os.path.join(selected_folder, original_name)
            temp_path = os.path.join(temp_dir, original_name)

            status_label.config(text=f"Preparing: {original_name}")
            prog_win.update()
            shutil.copy2(src_path, temp_path)

            current_step += 1
            prog_bar["value"] = current_step
            prog_win.update()

        for target_name, source_name in zip(
            selected_filenames, assigned_sources
        ):
            status_label.config(text=f"Writing: {target_name}")
            temp_source_path = os.path.join(temp_dir, source_name)
            dest_path = os.path.join(selected_folder, target_name)

            shutil.copy2(temp_source_path, dest_path)

            current_step += 1
            prog_bar["value"] = current_step
            prog_win.update()

        shutil.rmtree(temp_dir)
        prog_win.destroy()

        messagebox.showinfo(
            "Success",
            f"Successfully randomized {len(selected_filenames)} tracks!\nSeed used: {current_seed}",
        )

    except Exception as e:
        prog_win.destroy()
        messagebox.showerror(
            "Error", f"An error occurred during randomization:\n\n{e}"
        )


rand_frame = tk.Frame(right_frame)
rand_frame.pack(anchor="nw", fill=tk.X, pady=(10, 10))
btn_randomize = add_option_button(
    rand_frame, "Randomize", randomize_music, side=tk.LEFT, padx=20
)

main_frame.pack_forget()

root.mainloop()