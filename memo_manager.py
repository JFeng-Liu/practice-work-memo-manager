"""
Work Memo Manager - A simple desktop app for managing work memos.
Built with Python tkinter. No external packages required.

Data is saved to a local JSON file (memos.json) in the same folder.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

# Path to the JSON file that stores all memos
DATA_FILE = "memos.json"


def load_memos():
    """Load memos from the JSON file. Return an empty list if the file doesn't exist."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_memos(memos):
    """Write the full list of memos to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, indent=2, ensure_ascii=False)


class MemoApp:
    """Main application window for the Work Memo Manager."""

    def __init__(self, root):
        self.root = root
        self.root.title("Work Memo Manager")
        self.root.geometry("720x500")
        self.root.resizable(True, True)

        # Load existing memos from disk
        self.memos = load_memos()
        # Parallel list: maps listbox index -> memo ID (same order as listbox items)
        self._listbox_ids = []
        # Track the currently selected memo ID (None = nothing selected)
        self.selected_id = None

        self._build_ui()
        self._refresh_list()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Create and place all widgets in the main window."""
        # --- Left panel: search + memo list ---
        left_frame = tk.Frame(self.root, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        left_frame.pack_propagate(False)

        # Search box
        search_label = tk.Label(left_frame, text="Search:", anchor="w")
        search_label.pack(fill=tk.X)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        search_entry = tk.Entry(left_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(2, 8))

        # Memo list (Listbox + Scrollbar)
        list_label = tk.Label(left_frame, text="Saved Memos:", anchor="w")
        list_label.pack(fill=tk.X)

        list_container = tk.Frame(left_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_container, exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        list_scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=list_scrollbar.set)
        list_scrollbar.config(command=self.listbox.yview)

        # Bind selection event: when the user clicks a memo, show its details
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Delete button under the list
        delete_btn = tk.Button(
            left_frame, text="Delete Selected", command=self._delete_memo
        )
        delete_btn.pack(fill=tk.X, pady=(8, 0))

        # --- Right panel: input fields + detail view ---
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)

        # Title
        tk.Label(right_frame, text="Title:", anchor="w").pack(fill=tk.X)
        self.title_entry = tk.Entry(right_frame)
        self.title_entry.pack(fill=tk.X, pady=(2, 6))

        # Category
        tk.Label(right_frame, text="Category:", anchor="w").pack(fill=tk.X)
        self.category_entry = tk.Entry(right_frame)
        self.category_entry.pack(fill=tk.X, pady=(2, 6))

        # Content
        tk.Label(right_frame, text="Content:", anchor="w").pack(fill=tk.X)
        self.content_text = tk.Text(right_frame, height=12)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(2, 6))

        # Save button
        save_btn = tk.Button(
            right_frame, text="Save Memo", command=self._save_memo, bg="#4CAF50", fg="white"
        )
        save_btn.pack(fill=tk.X, pady=(0, 6))

        # New memo button: clears the form so the user can write a fresh memo
        clear_btn = tk.Button(
            right_frame, text="+ New Memo", command=self._clear_form
        )
        clear_btn.pack(fill=tk.X)

    # ------------------------------------------------------------------
    # Data actions
    # ------------------------------------------------------------------

    def _refresh_list(self):
        """Rebuild the listbox contents, applying the current search filter."""
        query = self.search_var.get().strip().lower()
        self.listbox.delete(0, tk.END)
        self._listbox_ids.clear()

        for memo in self.memos:
            title = memo.get("title", "")
            content = memo.get("content", "")
            # Match against title or content (case-insensitive)
            if query in title.lower() or query in content.lower():
                display = f"[{memo.get('category', '')}] {title}"
                self.listbox.insert(tk.END, display)
                # Keep a parallel list of IDs matching each listbox row
                self._listbox_ids.append(memo["id"])

    def _on_select(self, event):
        """Handle listbox selection: load the selected memo into the form."""
        selection = self.listbox.curselection()
        if not selection:
            return
        # Look up the memo ID from the parallel list using the selected index
        index = selection[0]
        if index >= len(self._listbox_ids):
            return
        memo_id = self._listbox_ids[index]

        # Find and display the memo
        for memo in self.memos:
            if memo["id"] == memo_id:
                self._clear_form()
                self.selected_id = memo_id
                self.title_entry.insert(0, memo.get("title", ""))
                self.category_entry.insert(0, memo.get("category", ""))
                self.content_text.insert("1.0", memo.get("content", ""))
                break

    def _save_memo(self):
        """Save the current form content as a new memo."""
        title = self.title_entry.get().strip()
        category = self.category_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        # Basic validation: title is required
        if not title:
            messagebox.showwarning("Missing Title", "Please enter a memo title.")
            return

        # Create a new memo with a unique ID
        new_id = max([m["id"] for m in self.memos], default=0) + 1
        memo = {
            "id": new_id,
            "title": title,
            "category": category,
            "content": content,
        }
        self.memos.append(memo)
        save_memos(self.memos)

        self._clear_form()
        self._refresh_list()
        messagebox.showinfo("Saved", f'Memo "{title}" has been saved.')

    def _delete_memo(self):
        """Delete the currently selected memo after confirmation."""
        if self.selected_id is None:
            messagebox.showinfo("Nothing Selected", "Please select a memo to delete.")
            return

        # Find the memo to get its title for the confirmation message
        target = next((m for m in self.memos if m["id"] == self.selected_id), None)
        if target is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f'Delete memo "{target["title"]}"?\nThis cannot be undone.',
        )
        if not confirmed:
            return

        # Remove from the in-memory list and save to disk
        self.memos = [m for m in self.memos if m["id"] != self.selected_id]
        save_memos(self.memos)

        self.selected_id = None
        self._clear_form()
        self._refresh_list()

    def _clear_form(self):
        """Reset all input fields to empty and clear the selection."""
        self.selected_id = None
        self.title_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()
