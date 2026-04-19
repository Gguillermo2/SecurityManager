# Vista/home.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from controller.home_controller import HomeController
from Modelo.models import AdminUser

def start_home(admin_user: AdminUser, fernet_key: bytes):
    """Inicia la ventana principal"""
    home = HomeWindow(admin_user, fernet_key)
    home.run()


class HomeWindow:
    """Vista principal - Solo UI y eventos simples. Toda la lógica está en el controlador."""

    def __init__(self, admin_user: AdminUser, fernet_key: bytes):
        self.root = tk.Tk()
        self.root.title("Gestor de Contraseñas - Panel Principal")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Controlador (cerebro de la aplicación)
        self.controller = HomeController(admin_user, fernet_key)

        # Variables de la vista
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Todas")
        self.selected_account = None

        # Configuración
        self.setup_styles()
        self.create_widgets()

        # Carga inicial
        self.refresh_accounts_list()

        # Verificar sesión
        self.check_session()

    def setup_styles(self):
        """Configura los estilos visuales"""
        self.root.configure(bg='#1e1e1e')
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background='#1e1e1e', foreground='white', borderwidth=0)
        style.configure('Treeview', background='#2d2d2d', foreground='white', 
                        rowheight=25, fieldbackground='#2d2d2d')
        style.map('Treeview', background=[('selected', '#0d7377')])
        style.configure('Treeview.Heading', background='#252525', foreground='white')
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 11))

    def create_widgets(self):
        """Crea toda la interfaz"""
        self.create_header()
        
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)

        self.create_left_panel(main_container)
        self.create_right_panel(main_container)
        self.create_status_bar()

    # ====================== HEADER ======================
    def create_header(self):
        header_frame = tk.Frame(self.root, bg='#0d7377', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        inner_header = tk.Frame(header_frame, bg='#0d7377')
        inner_header.pack(expand=True, fill='both', padx=20)

        # Título
        tk.Label(inner_header, text="🔐 Gestor de Contraseñas",
                    bg='#0d7377', fg='white', font=('Arial', 16, 'bold')).pack(side='left', pady=15)

        # Usuario y Logout
        right_frame = tk.Frame(inner_header, bg='#0d7377')
        right_frame.pack(side='right', fill='y')

        tk.Label(right_frame, text=f"👤 {self.controller.admin_user.username}",
                    bg='#0d7377', fg='white', font=('Arial', 11)).pack(side='left', padx=20, pady=15)

        tk.Button(right_frame, text="Cerrar Sesión", command=self.logout,
                    bg='#d32f2f', fg='white', font=('Arial', 10), padx=15, pady=5,
                    cursor='hand2', relief='flat').pack(side='right', pady=15)

    # ====================== PANEL IZQUIERDO ======================
    def create_left_panel(self, parent):
        left_frame = tk.Frame(parent, bg='#252525', width=400)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        left_frame.pack_propagate(False)

        # Controles superiores
        controls_frame = tk.Frame(left_frame, bg='#252525')
        controls_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(controls_frame, text="Cuentas Guardadas", style='Title.TLabel').pack(side='left')

        tk.Button(controls_frame, text="+ Nueva", command=self.show_add_account_dialog,
                    bg='#14ae5c', fg='white', font=('Arial', 10), padx=15, pady=5,
                    cursor='hand2', relief='flat').pack(side='right')

        # Búsqueda y filtro
        search_frame = tk.Frame(left_frame, bg='#252525')
        search_frame.pack(fill='x', padx=10, pady=(0, 10))

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 11))
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))

        categories = self.controller.get_all_categories()
        category_combo = ttk.Combobox(search_frame, textvariable=self.category_var,
                                        values=categories, state='readonly', width=15)
        category_combo.pack(side='right')
        category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_accounts())

        # Treeview
        tree_frame = tk.Frame(left_frame, bg='#252525')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.accounts_tree = ttk.Treeview(tree_frame, columns=('Usuario', 'Categoría'),
                                            show='tree headings', yscrollcommand=scrollbar.set)
        self.accounts_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.accounts_tree.yview)

        self.accounts_tree.heading('#0', text='Plataforma')
        self.accounts_tree.heading('Usuario', text='Usuario/Email')
        self.accounts_tree.heading('Categoría', text='Categoría')

        self.accounts_tree.column('#0', width=150)
        self.accounts_tree.column('Usuario', width=150)
        self.accounts_tree.column('Categoría', width=100)

        # Eventos
        self.search_var.trace('w', lambda *args: self.filter_accounts())
        self.accounts_tree.bind('<<TreeviewSelect>>', self.on_account_select)
        self.accounts_tree.bind('<Double-Button-1>', lambda e: self.show_password())

    # ====================== PANEL DERECHO ======================
    def create_right_panel(self, parent):
        right_frame = tk.Frame(parent, bg='#252525', width=350)
        right_frame.pack(side='right', fill='both', padx=(5, 0))
        right_frame.pack_propagate(False)

        ttk.Label(right_frame, text="Detalles de la Cuenta", style='Title.TLabel')\
            .pack(padx=20, pady=(20, 10))

        self.details_frame = tk.Frame(right_frame, bg='#252525')
        self.details_frame.pack(fill='both', expand=True, padx=20)

        self.no_selection_label = ttk.Label(self.details_frame,
                                            text="Seleccione una cuenta\npara ver los detalles",
                                            style='Subtitle.TLabel', justify='center')
        self.no_selection_label.pack(expand=True)

        self.account_details_frame = tk.Frame(self.details_frame, bg='#252525')

        # Acciones
        actions_frame = tk.Frame(right_frame, bg='#252525')
        actions_frame.pack(fill='x', padx=20, pady=20)

        self.edit_btn = tk.Button(actions_frame, text="✏️ Editar", command=self.edit_account,
                                    bg='#1976d2', fg='white', font=('Arial', 10), padx=15, pady=8,
                                    cursor='hand2', relief='flat', state='disabled')
        self.edit_btn.pack(side='left', padx=(0, 10))

        self.delete_btn = tk.Button(actions_frame, text="🗑️ Eliminar", command=self.delete_account,
                                    bg='#d32f2f', fg='white', font=('Arial', 10), padx=15, pady=8,
                                    cursor='hand2', relief='flat', state='disabled')
        self.delete_btn.pack(side='left')

        tk.Button(actions_frame, text="🔐 Generar Contraseña", command=self.generate_password,
                    bg='#673ab7', fg='white', font=('Arial', 10), padx=15, pady=8,
                    cursor='hand2', relief='flat').pack(side='right')

    # ====================== BARRA DE ESTADO ======================
    def create_status_bar(self):
        status_frame = tk.Frame(self.root, bg='#1a1a1a', height=30)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="", bg='#1a1a1a', fg='#888', font=('Arial', 9))
        self.status_label.pack(side='left', padx=10, pady=5)

        self.time_label = tk.Label(status_frame, text="", bg='#1a1a1a', fg='#888', font=('Arial', 9))
        self.time_label.pack(side='right', padx=10, pady=5)

        self.update_status_bar()
        self.update_time()

    # ====================== MÉTODOS DE ACTUALIZACIÓN ======================

    def refresh_accounts_list(self):
        """Actualiza la lista completa de cuentas"""
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)

        accounts = self.controller.get_filtered_accounts(
            search=self.search_var.get(),
            category=self.category_var.get()
        )

        for account in accounts:
            self.accounts_tree.insert('', 'end', iid=account.id,
                                        text=account.platform,
                                        values=(account.email_or_username, account.category))

        self.update_status_bar()

    def filter_accounts(self):
        self.refresh_accounts_list()

    def on_account_select(self, event):
        selection = self.accounts_tree.selection()
        if not selection:
            return

        account_id = selection[0]
        self.selected_account = self.controller.select_account(account_id)

        if self.selected_account:
            self.show_account_details()
            self.edit_btn.config(state='normal')
            self.delete_btn.config(state='normal')

    def update_status_bar(self):
        summary = self.controller.get_accounts_summary()
        total = summary['total']
        status_text = f"Total de cuentas: {total}"

        if summary['by_category']:
            categories_text = " | ".join([f"{cat}: {count}" 
                                        for cat, count in summary['by_category'].items()])
            status_text += f" | {categories_text}"

        self.status_label.config(text=status_text)

    def update_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    # ====================== DETALLES Y CONTRASEÑA ======================

    def show_account_details(self):
        if not self.selected_account:
            return

        self.no_selection_label.pack_forget()
        for widget in self.account_details_frame.winfo_children():
            widget.destroy()

        self.account_details_frame.pack(fill='both', expand=True)

        details = [
            ("Plataforma:", self.selected_account.platform),
            ("Usuario/Email:", self.selected_account.email_or_username),
            ("Categoría:", self.selected_account.category),
            ("Contraseña:", "*" * 12),
        ]

        for label_text, value in details:
            row = tk.Frame(self.account_details_frame, bg='#252525')
            row.pack(fill='x', pady=5)

            tk.Label(row, text=label_text, bg='#252525', fg='#888', font=('Arial', 10), width=15, anchor='w').pack(side='left')

            if label_text == "Contraseña:":
                self.password_label = tk.Label(row, text=value, bg='#252525', fg='white',
                                                font=('Arial', 10, 'bold'))
                self.password_label.pack(side='left', padx=(0, 10))

                tk.Button(row, text="👁️", command=self.toggle_password,
                            bg='#252525', fg='white', font=('Arial', 8), cursor='hand2', relief='flat').pack(side='left')
            else:
                tk.Label(row, text=value, bg='#252525', fg='white', font=('Arial', 10, 'bold')).pack(side='left')

        # Notas
        if self.selected_account.notes:
            notes_frame = tk.Frame(self.account_details_frame, bg='#252525')
            notes_frame.pack(fill='x', pady=(15, 5))
            tk.Label(notes_frame, text="Notas:", bg='#252525', fg='#888', font=('Arial', 10), anchor='w').pack(anchor='w')
            notes_text = tk.Text(notes_frame, bg='#2d2d2d', fg='white', font=('Arial', 9), height=4, wrap='word', relief='flat')
            notes_text.pack(fill='x', pady=5)
            notes_text.insert('1.0', self.selected_account.notes)
            notes_text.config(state='disabled')

        # Fechas
        if self.selected_account.created_at:
            dates_frame = tk.Frame(self.account_details_frame, bg='#252525')
            dates_frame.pack(fill='x', pady=(15, 0))
            tk.Label(dates_frame, text=f"Creada: {self.selected_account.created_at[:10]}",
                        bg='#252525', fg='#666', font=('Arial', 8)).pack(anchor='w')
            if self.selected_account.updated_at:
                tk.Label(dates_frame, text=f"Actualizada: {self.selected_account.updated_at[:10]}",
                            bg='#252525', fg='#666', font=('Arial', 8)).pack(anchor='w')

    def toggle_password(self):
        if self.password_label.cget('text').startswith('*'):
            password = self.controller.get_decrypted_password(self.selected_account.id)
            self.password_label.config(text=password)
        else:
            self.password_label.config(text='*' * 12)

    def show_password(self):
        if not self.selected_account:
            return
        # (Diálogo de mostrar contraseña - código igual que antes, pero usando controller)
        dialog = tk.Toplevel(self.root)
        dialog.title("Contraseña")
        dialog.geometry("400x200")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()

        # Centrar...
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text=f"Contraseña de {self.selected_account.platform}",
                    bg='#1e1e1e', fg='white', font=('Arial', 12, 'bold')).pack(pady=20)

        pass_frame = tk.Frame(dialog, bg='#2d2d2d', relief='solid', bd=1)
        pass_frame.pack(padx=20, pady=10)

        password = self.controller.get_decrypted_password(self.selected_account.id)
        password_text = tk.Text(pass_frame, bg='#2d2d2d', fg='white', font=('Consolas', 14),
                                height=1, width=30, relief='flat')
        password_text.pack(padx=10, pady=10)
        password_text.insert('1.0', password)
        password_text.config(state='disabled')

        def copy_password():
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            messagebox.showinfo("Copiado", "Contraseña copiada", parent=dialog)
            dialog.destroy()

        tk.Button(dialog, text="📋 Copiar", command=copy_password,
                    bg='#0d7377', fg='white', font=('Arial', 10), padx=20, pady=8,
                    cursor='hand2', relief='flat').pack(pady=10)

    # ====================== DIÁLOGOS ======================

    def show_add_account_dialog(self):
        """Diálogo para agregar nueva cuenta"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Nueva Cuenta")
        dialog.geometry("520x620")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(dialog, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=30, pady=25)

        tk.Label(main_frame, text="Nueva Cuenta", bg='#1e1e1e', fg='white',
                    font=('Arial', 16, 'bold')).pack(pady=(0, 25))
        
        # Variables
        platform = tk.StringVar()
        user = tk.StringVar()
        password = tk.StringVar()
        category = tk.StringVar(value="General")
        notes = tk.StringVar()
        
        # Campos 
        self._create_labeled_entry(main_frame, "Plataforma:", platform)
        self._create_labeled_entry(main_frame, "Usuario / Email:", user)
        self._create_labeled_entry(main_frame, "Contraseña:", password, show="*")

        # Categoría
        cat_frame = tk.Frame(main_frame, bg='#1e1e1e')
        cat_frame.pack(fill='x', pady=8)
        tk.Label(cat_frame, text="Categoría:", bg='#1e1e1e', fg='#888', width=15, anchor='w').pack(side='left')
        ttk.Combobox(cat_frame, textvariable=category, 
                    values=["General", "Redes Sociales", "Bancos", "Correo", "Otros"],
                    state='readonly').pack(side='left', fill='x', expand=True)
        
        # Notas
        tk.Label(main_frame, text="Notas:", bg='#1e1e1e', fg='#888', anchor='w').pack(fill='x', pady=(15,5))
        notes_text = tk.Text(main_frame, height=6, bg='#2d2d2d', fg='white', relief='flat')
        notes_text.pack(fill='x', pady=5)

        # Botones
        btn_frame = tk.Frame(main_frame, bg='#1e1e1e')
        btn_frame.pack(fill='x', pady=20)

        tk.Button(btn_frame, text="Guardar", command=lambda: self._save_new_account(
            dialog, platform, user, password, category, notes_text),
            bg='#14ae5c', fg='white', font=('Arial', 11, 'bold'), padx=25, pady=10).pack(side='right', padx=5)

        tk.Button(btn_frame, text="Cancelar", command=dialog.destroy,
                    bg='#555', fg='white', font=('Arial', 11), padx=25, pady=10).pack(side='right', padx=5)

    def _create_labeled_entry(self, parent, label_text, var, show=None):
        frame = tk.Frame(parent, bg='#1e1e1e')
        frame.pack(fill='x', pady=8)
        tk.Label(frame, text=label_text, bg='#1e1e1e', fg='#888', width=15, anchor='w').pack(side='left')
        entry = ttk.Entry(frame, textvariable=var, show=show, font=('Arial', 11))
        entry.pack(side='left', fill='x', expand=True, padx=(10, 0))
        return entry
    

    def _save_new_account(self, dialog, platform, user, password, category, notes):
        platform = platform.get().strip()
        user = user.get().strip()
        password = password.get().strip()
        category = category.get()
        notes = notes.get('1.0', 'end-1c').strip()

        if not all([platform, user, password]):
            messagebox.showerror("Error", "Complete los campos obligatorios", parent=dialog)
            return
        try:
            self.controller.create_account(platform, user, password, category, notes)
            messagebox.showinfo("Éxito", f"Cuenta '{platform}' agregada correctamente", parent=dialog)
            self.refresh_accounts_list()
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}", parent=dialog)

    def edit_account(self):
        if not self.selected_account:
            messagebox.showwarning("Advertencia", "Seleccione una cuenta para editar.", parent=self.root)
            return


    def delete_account(self):
        if not self.selected_account:
            messagebox.showwarning("Advertencia", "Seleccione una cuenta para eliminar.", parent=self.root)
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{self.selected_account.platform}'?"):
            if self.controller.delete_account(self.selected_account.id):
                messagebox.showinfo("Éxito", "Cuenta eliminada")
                self.refresh_accounts_list()
                self.clear_details_panel()
            else:
                messagebox.showerror("Error", "No se pudo eliminar la cuenta")

    def generate_password(self):
        """Diálogo simple para generar contraseña"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Generador de Contraseña")
        dialog.geometry("400x280")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()

        length_var = tk.IntVar(value=16)

        tk.Label(dialog, text="Generar Contraseña Fuerte", bg='#1e1e1e', fg='white',
                font=('Arial', 14, 'bold')).pack(pady=20)

        tk.Label(dialog, text="Longitud:", bg='#1e1e1e', fg='#888').pack()
        ttk.Scale(dialog, from_=8, to=32, variable=length_var, orient='horizontal').pack(fill='x', padx=40, pady=10)

        password_var = tk.StringVar(value=self.controller.suggest_strong_password(length_var.get()))

        pass_entry = ttk.Entry(dialog, textvariable=password_var, font=('Consolas', 14), justify='center')
        pass_entry.pack(fill='x', padx=40, pady=15)

        def regenerate():
            password_var.set(self.controller.suggest_strong_password(length_var.get()))

        tk.Button(dialog, text="Generar Nueva", command=regenerate,
                    bg='#673ab7', fg='white').pack(pady=5)

        tk.Button(dialog, text="Copiar al Portapapeles", 
                    command=lambda: self._copy_to_clipboard(password_var.get(), dialog),
                    bg='#0d7377', fg='white', font=('Arial', 11, 'bold')).pack(pady=10)

    def _copy_to_clipboard(self, text: str, dialog):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copiado", "Contraseña copiada al portapapeles", parent=dialog)
        dialog.destroy()

    def clear_details_panel(self):
        self.account_details_frame.pack_forget()
        self.no_selection_label.pack(expand=True)
        self.edit_btn.config(state='disabled')
        self.delete_btn.config(state='disabled')
        self.selected_account = None

    # ====================== SESIÓN ======================

    def check_session(self):
        if not self.controller.is_session_valid():
            messagebox.showwarning("Sesión expirada", "Su sesión ha expirado. Inicie sesión nuevamente.")
            self.logout()
        else:
            self.root.after(60000, self.check_session)

    def logout(self):
        self.controller.logout()
        self.root.destroy()
        from Vista.login import start_login
        start_login(lambda u, k: start_home(u, k))

    def run(self):
        self.root.mainloop()