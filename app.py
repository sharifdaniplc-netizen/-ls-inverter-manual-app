import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import fitz  # PyMuPDF

class InverterSuperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LS Inverter SV-iG5A Pro Analyzer - Search Fixed")
        self.root.geometry("1300x850")

        self.pdf_path = "LS_Inverter_SV-IG5A_Series_User_Manual.pdf"
        self.img_dir = "my_pages_rendered"
        self.doc = None
        
        self.zoom_level = 1.0
        self.current_page_num = 1
        self.bookmarks = []

        self.load_pdf()
        self.ensure_page_images_exist()
        self.setup_ui()

    def load_pdf(self):
        if os.path.exists(self.pdf_path):
            self.doc = fitz.open(self.pdf_path)
        else:
            messagebox.showerror("Error", f"PDF manual not found at {self.pdf_path}!")

    def ensure_page_images_exist(self):
        # مطمئن شویم پوشه رندر عکس صفحات وجود دارد
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        
        if self.doc:
            for i in range(len(self.doc)):
                img_path = os.path.join(self.img_dir, f"page_{i+1}.png")
                if not os.path.exists(img_path):
                    page = self.doc[i]
                    pix = page.get_pixmap(dpi=150)
                    pix.save(img_path)

    def setup_ui(self):
        # --- TOP BAR (Search & Quick Actions) ---
        self.top_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        self.top_bar.pack(side="top", fill="x")

        tk.Label(self.top_bar, text="🔍 Search:", fg="white", bg="#2c3e50", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.search_entry = tk.Entry(self.top_bar, font=("Arial", 11), width=25)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        tk.Button(self.top_bar, text="Search Text", command=self.perform_search, bg="#27ae60", fg="white").pack(side="left", padx=2)
        
        tk.Button(self.top_bar, text="⭐ Bookmark Page", command=self.add_bookmark, bg="#f39c12", fg="white").pack(side="left", padx=15)
        tk.Button(self.top_bar, text="💾 Save Image", command=self.save_current_page, bg="#2980b9", fg="white").pack(side="left", padx=2)
        tk.Button(self.top_bar, text="🖨️ Print View", command=self.print_current_page, bg="#8e44ad", fg="white").pack(side="left", padx=2)

        # --- MAIN PANED WINDOW ---
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4)
        self.paned_window.pack(fill="both", expand=True)

        # 1. Left Panel (Tabs: Contents, Search Results, Bookmarks, Fault Codes)
        self.left_container = tk.Frame(self.paned_window, width=350, bg="#ecf0f1")
        self.paned_window.add(self.left_container)

        self.left_tabs = ttk.Notebook(self.left_container)
        self.left_tabs.pack(fill="both", expand=True)

        # Tab 1: TOC
        self.toc_frame = tk.Frame(self.left_tabs, bg="#ecf0f1")
        self.toc_tree = ttk.Treeview(self.toc_frame, columns=("page"), show="tree headings")
        self.toc_tree.heading("#0", text="Chapter / Topic")
        self.toc_tree.heading("page", text="Page")
        self.toc_tree.column("page", width=50, stretch=False)
        self.toc_tree.pack(fill="both", expand=True)
        self.toc_tree.bind("<<TreeviewSelect>>", self.on_toc_click)
        self.left_tabs.add(self.toc_frame, text="Contents")

        # Tab 2: Results
        self.search_frame = tk.Frame(self.left_tabs, bg="#ecf0f1")
        self.search_listbox = tk.Listbox(self.search_frame, font=("Arial", 10))
        self.search_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.search_listbox.bind('<<ListboxSelect>>', self.on_search_click)
        self.left_tabs.add(self.search_frame, text="Results")

        # Tab 3: Bookmarks
        self.bm_frame = tk.Frame(self.left_tabs, bg="#ecf0f1")
        self.bm_listbox = tk.Listbox(self.bm_frame, font=("Arial", 10))
        self.bm_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.bm_listbox.bind('<<ListboxSelect>>', self.on_bm_click)
        self.left_tabs.add(self.bm_frame, text="Bookmarks")

        # Tab 4: Fault Codes Quick Lookup
        self.fault_frame = tk.Frame(self.left_tabs, bg="#ecf0f1")
        self.fault_listbox = tk.Listbox(self.fault_frame, font=("Arial", 10))
        self.fault_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.fault_listbox.bind('<<ListboxSelect>>', self.on_fault_click)
        self.load_fault_codes()
        self.left_tabs.add(self.fault_frame, text="Faults ⚠️")

        # 2. Right Panel (Viewer)
        self.view_container = tk.Frame(self.paned_window, bg="#bdc3c7")
        self.paned_window.add(self.view_container)

        # Zoom Controls
        self.ctrl_bar = tk.Frame(self.view_container, bg="#34495e")
        self.ctrl_bar.pack(side="top", fill="x")
        
        tk.Button(self.ctrl_bar, text="➕ Zoom In", command=lambda: self.change_zoom(1.2)).pack(side="left", padx=5, pady=2)
        tk.Button(self.ctrl_bar, text="➖ Zoom Out", command=lambda: self.change_zoom(0.8)).pack(side="left", padx=5, pady=2)
        tk.Button(self.ctrl_bar, text="🔄 Reset", command=self.reset_zoom).pack(side="left", padx=5, pady=2)
        self.zoom_label = tk.Label(self.ctrl_bar, text="100%", bg="#34495e", fg="white")
        self.zoom_label.pack(side="right", padx=10)

        # Canvas with Scrollbars
        self.canvas_frame = tk.Frame(self.view_container)
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.config(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.current_image_obj = None
        self.load_toc()
        self.display_page(1)

    def load_toc(self):
        if not self.doc: return
        toc = self.doc.get_toc()
        for level, title, page in toc:
            indent = "  " * (level - 1)
            self.toc_tree.insert("", "end", text=f"{indent}{title}", values=(page,))

    def load_fault_codes(self):
        faults = [
            ("OC - Overcurrent", 163),
            ("OV - Overvoltage", 163),
            ("LV - Low Voltage", 163),
            ("OHT - Inverter Overheat", 163),
            ("IOLT - Inverter Overload", 167),
            ("OLT - Motor Overload", 145),
            ("GFT - Ground Fault", 163),
            ("EEP - EEPROM Error", 164),
            ("HWT - Hardware Trouble", 164)
        ]
        for name, page in faults:
            self.fault_listbox.insert(tk.END, f"{name} (Page {page})")

    def on_toc_click(self, event):
        sel = self.toc_tree.selection()
        if sel:
            page_num = self.toc_tree.item(sel[0], "values")[0]
            if page_num: 
                self.display_page(int(page_num))

    def perform_search(self):
        query = self.search_entry.get().strip().lower()
        if not query or not self.doc: return
        
        self.search_listbox.delete(0, tk.END)
        found_count = 0
        
        for i in range(len(self.doc)):
            page = self.doc[i]
            text = page.get_text("text").lower()
            if query in text:
                self.search_listbox.insert(tk.END, f"Page {i+1}")
                found_count += 1
                
        if found_count == 0:
            self.search_listbox.insert(tk.END, "No results found.")
        else:
            # خودکار سوئیچ به تب Results
            self.left_tabs.select(1)

    def on_search_click(self, event):
        sel = self.search_listbox.curselection()
        if sel:
            item = self.search_listbox.get(sel[0])
            if "Page" in item:
                page_num = int(item.split(" ")[1])
                self.display_page(page_num)

    def add_bookmark(self):
        bm_text = f"Page {self.current_page_num}"
        if self.current_page_num not in self.bookmarks:
            self.bookmarks.append(self.current_page_num)
            self.bm_listbox.insert(tk.END, bm_text)
            messagebox.showinfo("Bookmark", f"Page {self.current_page_num} added to bookmarks!")

    def on_bm_click(self, event):
        sel = self.bm_listbox.curselection()
        if sel:
            item = self.bm_listbox.get(sel[0])
            page_num = int(item.split(" ")[1])
            self.display_page(page_num)

    def on_fault_click(self, event):
        sel = self.fault_listbox.curselection()
        if sel:
            item = self.fault_listbox.get(sel[0])
            page_num = int(item.split("Page ")[1].replace(")", ""))
            self.display_page(page_num)

    def save_current_page(self):
        if not self.current_page_num: return
        img_path = os.path.join(self.img_dir, f"page_{self.current_page_num}.png")
        if os.path.exists(img_path):
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
            if file_path:
                img = Image.open(img_path)
                img.save(file_path)
                messagebox.showinfo("Success", "Page saved successfully!")

    def print_current_page(self):
        messagebox.showinfo("Print", f"Print feature triggered for Page {self.current_page_num}")

    def display_page(self, page_num):
        self.current_page_num = page_num
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
        self.render_image()

    def render_image(self):
        if not self.current_page_num: return
        img_path = os.path.join(self.img_dir, f"page_{self.current_page_num}.png")
        if os.path.exists(img_path):
            img = Image.open(img_path)
            w, h = img.size
            new_size = (int(w * self.zoom_level), int(h * self.zoom_level))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            self.current_image_obj = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.current_image_obj)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def change_zoom(self, factor):
        self.zoom_level *= factor
        self.zoom_label.config(text=f"{int(self.zoom_level*100)}%")
        self.render_image()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
        self.render_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = InverterSuperApp(root)
    root.mainloop()
