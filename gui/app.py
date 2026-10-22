import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from organizer.service import FileOrganizer

class FileOrganizerApp:
    def __init__(self):
        self.service=FileOrganizer(); self.root=tk.Tk(); self.root.title('Advanced File Organizer'); self.root.geometry('1100x680'); self.root.minsize(850,540)
        self.folder_var=tk.StringVar(); self.recursive=tk.BooleanVar(value=False); self.pattern=tk.StringVar(value='{index:03d}_{name}'); self.status=tk.StringVar(value='Choose a test folder to begin.')
        self.build()
    def build(self):
        main=ttk.Frame(self.root,padding=12); main.pack(fill='both',expand=True)
        ttk.Label(main,text='Advanced File Organizer',font=('Segoe UI',18,'bold')).pack(anchor='w')
        ttk.Label(main,text='Automatic categorization • SHA-256 duplicate detection • Batch rename • Undo journal').pack(anchor='w',pady=(2,10))
        bar=ttk.Frame(main); bar.pack(fill='x',pady=(0,8)); ttk.Label(bar,text='Folder:').pack(side='left')
        ttk.Entry(bar,textvariable=self.folder_var).pack(side='left',fill='x',expand=True,padx=7); ttk.Button(bar,text='Browse…',command=self.browse).pack(side='left')
        ttk.Checkbutton(bar,text='Include subfolders',variable=self.recursive).pack(side='left',padx=8)
        actions=ttk.LabelFrame(main,text='Operations',padding=7); actions.pack(fill='x',pady=6)
        for i,(label,cmd) in enumerate([('Scan',self.scan),('Preview categorize',self.preview_categorize),('Categorize',self.categorize),('Find duplicates',self.find_duplicates),('Move duplicate copies',self.move_duplicates),('Undo last',self.undo)]):
            ttk.Button(actions,text=label,command=cmd).grid(row=0,column=i,padx=3,pady=3,sticky='ew'); actions.columnconfigure(i,weight=1)
        ren=ttk.LabelFrame(main,text='Batch rename pattern',padding=7); ren.pack(fill='x',pady=6)
        ttk.Label(ren,text='Pattern:').pack(side='left'); ttk.Entry(ren,textvariable=self.pattern,width=28).pack(side='left',padx=6)
        ttk.Label(ren,text='Tokens: {name}, {ext}, {index}, {date}; example {index:03d}_{name}').pack(side='left',padx=4)
        ttk.Button(ren,text='Preview',command=self.preview_rename).pack(side='left',padx=4); ttk.Button(ren,text='Rename',command=self.rename).pack(side='left')
        cols=('name','category','size','modified','path'); self.tree=ttk.Treeview(main,columns=cols,show='headings',selectmode='extended')
        for c,title,w in [('name','File name',190),('category','Category',110),('size','Bytes',80),('modified','Modified',150),('path','Source / destination',500)]: self.tree.heading(c,text=title); self.tree.column(c,width=w,anchor='w')
        y=ttk.Scrollbar(main,orient='vertical',command=self.tree.yview); self.tree.configure(yscrollcommand=y.set); self.tree.pack(side='left',fill='both',expand=True); y.pack(side='left',fill='y')
        ttk.Label(main,textvariable=self.status,relief='sunken',anchor='w').pack(fill='x',pady=(8,0))
    def run(self): self.root.mainloop()
    def browse(self):
        p=filedialog.askdirectory(title='Choose a folder');
        if p: self.folder_var.set(p); self.scan()
    def folder(self):
        p=self.folder_var.get().strip()
        if not p: raise ValueError('Choose a folder first.')
        return p
    def safe(self,fn):
        try: fn()
        except Exception as e: messagebox.showerror('Operation failed',str(e)); self.status.set('Operation failed. Check logs/organizer.log.')
    def display(self,rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            path=r.get('path') or f"{r.get('source','')}  →  {r.get('target','')}"
            self.tree.insert('','end',values=(r.get('name',Path(r.get('source','')).name),r.get('category',''),r.get('size',''),r.get('modified',''),path))
        self.status.set(f'{len(rows)} item(s) displayed.')
    def scan(self): self.safe(lambda:self.display(self.service.scan(self.folder(),self.recursive.get())))
    def preview_categorize(self): self.safe(lambda:self.display(self.service.categorize_preview(self.folder(),self.recursive.get())))
    def categorize(self):
        def go():
            if messagebox.askyesno('Confirm','Move files into category folders? Review Preview categorize first. Undo is available for the latest operation.'):
                op=self.service.categorize(self.folder(),self.recursive.get()); self.status.set(f"Categorized {len(op['moves'])} files."); self.display(self.service.scan(self.folder(),self.recursive.get()))
        self.safe(go)
    def find_duplicates(self):
        def go():
            groups=self.service.find_duplicates(self.folder(),self.recursive.get()); rows=[]
            for g in groups:
                for p in g['files']: rows.append({'name':Path(p).name,'category':'Duplicate','size':g['size'],'path':p})
            self.display(rows); self.status.set(f'Found {len(groups)} duplicate group(s).')
        self.safe(go)
    def move_duplicates(self):
        def go():
            groups=self.service.find_duplicates(self.folder(),self.recursive.get())
            if not groups: messagebox.showinfo('Duplicates','No duplicates found.'); return
            if messagebox.askyesno('Confirm','Move extra copies to _duplicates recovery folders? No permanent deletion occurs.'):
                op=self.service.remove_duplicates(groups); self.status.set(f"Moved {len(op['moves'])} duplicate copy/copies."); self.display(self.service.scan(self.folder(),self.recursive.get()))
        self.safe(go)
    def preview_rename(self): self.safe(lambda:self.display(self.service.rename_preview(self.folder(),self.pattern.get(),self.recursive.get())))
    def rename(self):
        def go():
            preview=self.service.rename_preview(self.folder(),self.pattern.get(),self.recursive.get())
            if not preview: messagebox.showinfo('Rename','No files found.'); return
            if messagebox.askyesno('Confirm rename',f'Rename {len(preview)} file(s)? Preview first to check names.'):
                op=self.service.batch_rename(self.folder(),self.pattern.get(),self.recursive.get()); self.status.set(f"Renamed {len(op['moves'])} files."); self.display(self.service.scan(self.folder(),self.recursive.get()))
        self.safe(go)
    def undo(self):
        def go(): messagebox.showinfo('Undo',self.service.undo_last()); self.display(self.service.scan(self.folder(),self.recursive.get()))
        self.safe(go)
