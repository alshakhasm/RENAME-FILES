"""
SIMPLE GUI - No bullshit, just works
Select file/folder → Preview → Execute
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
import os

class SimpleDateRenamerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Date Prefix Renamer")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        self.selected_path = None
        
        self._create_ui()
        
    def _create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Compact title
        title = ttk.Label(main_frame, text="📅 Date Prefix Renamer", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 15))
        
        # Step 1: Select file/folder (compact)
        step1_frame = ttk.LabelFrame(main_frame, text="1️⃣ Select", padding="8")
        step1_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.selected_label = ttk.Label(step1_frame, text="No selection", foreground="gray", font=("Arial", 9))
        self.selected_label.pack(pady=(0, 8))
        
        button_frame = ttk.Frame(step1_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="📄 File", command=self._select_file, width=8).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(button_frame, text="📁 Folder", command=self._select_folder, width=8).pack(side=tk.LEFT)
        
        # Step 2: Preview (compact)
        step2_frame = ttk.LabelFrame(main_frame, text="2️⃣ Preview", padding="8")
        step2_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.preview_button = ttk.Button(step2_frame, text="👁️ Preview Changes", 
                                       command=self._preview_changes, state='disabled')
        self.preview_button.pack(pady=(0, 8))
        
        # Compact preview text area
        self.preview_text = tk.Text(step2_frame, height=6, state='disabled', 
                                   font=("Courier", 9), wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Step 3: Execute (compact)
        step3_frame = ttk.LabelFrame(main_frame, text="3️⃣ Execute", padding="8")
        step3_frame.pack(fill=tk.X)
        
        self.execute_button = ttk.Button(step3_frame, text="🚀 Execute Changes", 
                                       command=self._execute_changes, state='disabled')
        self.execute_button.pack(pady=5)
        
        self.changes_previewed = False
        
    def _select_file(self):
        """Select a single file"""
        file_path = filedialog.askopenfilename(
            title="Select File to Rename",
            filetypes=[("All files", "*.*")]
        )
        if file_path:
            self.selected_path = Path(file_path)
            name = self.selected_path.name
            if len(name) > 30:
                name = name[:27] + "..."
            self.selected_label.config(text=f"📄 {name}", foreground="black")
            self.preview_button.config(state='normal')
            self.changes_previewed = False
            self.execute_button.config(state='disabled')
            
    def _select_folder(self):
        """Select a folder"""
        folder_path = filedialog.askdirectory(title="Select Folder to Rename")
        if folder_path:
            self.selected_path = Path(folder_path)
            name = self.selected_path.name
            if len(name) > 30:
                name = name[:27] + "..."
            self.selected_label.config(text=f"📁 {name}", foreground="black")
            self.preview_button.config(state='normal')
            self.changes_previewed = False
            self.execute_button.config(state='disabled')
            
    def _preview_changes(self):
        """Show what will be renamed"""
        if not self.selected_path:
            return
            
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        
        try:
            # Get current date in DDMMYYYY format
            today = datetime.now().strftime("%d%m%Y")
            
            if self.selected_path.is_file():
                # Single file
                old_name = self.selected_path.name
                new_name = f"{today}_{old_name}"
                new_path = self.selected_path.parent / new_name
                
                self.preview_text.insert(tk.END, "FILE RENAME:\n")
                self.preview_text.insert(tk.END, f"From: {old_name}\n")
                self.preview_text.insert(tk.END, f"To:   {new_name}\n")
                self.preview_text.insert(tk.END, f"Location: {self.selected_path.parent}\n")
                
                # Store for execution
                self.rename_plan = [(self.selected_path, new_path)]
                
            else:
                # Folder
                old_name = self.selected_path.name
                new_name = f"{today}_{old_name}"
                new_path = self.selected_path.parent / new_name
                
                self.preview_text.insert(tk.END, "FOLDER RENAME:\n")
                self.preview_text.insert(tk.END, f"From: {old_name}\n")
                self.preview_text.insert(tk.END, f"To:   {new_name}\n")
                self.preview_text.insert(tk.END, f"Location: {self.selected_path.parent}\n")
                
                # Store for execution
                self.rename_plan = [(self.selected_path, new_path)]
                
            self.preview_text.config(state='disabled')
            self.changes_previewed = True
            self.execute_button.config(state='normal')
            
        except Exception as e:
            self.preview_text.insert(tk.END, f"ERROR: {e}")
            self.preview_text.config(state='disabled')
            
    def _execute_changes(self):
        """Actually rename the file/folder"""
        if not self.changes_previewed:
            messagebox.showerror("Error", "Please preview changes first!")
            return
            
        # Confirm
        result = messagebox.askyesno(
            "Confirm Rename", 
            "Are you sure you want to rename the selected file/folder?\n\nThis cannot be undone!"
        )
        
        if not result:
            return
            
        try:
            success_count = 0
            errors = []
            
            for old_path, new_path in self.rename_plan:
                try:
                    if new_path.exists():
                        errors.append(f"Target already exists: {new_path.name}")
                        continue
                        
                    old_path.rename(new_path)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Failed to rename {old_path.name}: {e}")
            
            # Show results
            if success_count > 0 and not errors:
                messagebox.showinfo("Success", f"Successfully renamed {success_count} item(s)!")
                self._reset()
            elif success_count > 0 and errors:
                messagebox.showwarning("Partial Success", 
                                     f"Renamed {success_count} item(s).\n\nErrors:\n" + "\n".join(errors))
                self._reset()
            else:
                messagebox.showerror("Failed", "No items were renamed.\n\nErrors:\n" + "\n".join(errors))
                
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
            
    def _reset(self):
        """Reset the interface after successful rename"""
        self.selected_path = None
        self.selected_label.config(text="No selection", foreground="gray")
        self.preview_button.config(state='disabled')
        self.execute_button.config(state='disabled')
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state='disabled')
        self.changes_previewed = False
        
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    print("Simple Date Renamer GUI")
    print("======================")
    
    app = SimpleDateRenamerGUI()
    app.run()