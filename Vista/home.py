# Vista/home.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.account_manager import AccountManager
from core.session import SessionManager
from Modelo.models import AdminUser

# Función helper para iniciar la aplicación principal
def start_home(admin_user: AdminUser, fernet_key: bytes):
    """Inicia la ventana principal"""
    home = HomeWindow(admin_user, fernet_key)
    home.run()

class HomeWindow:
    def __init__(self, admin_user: AdminUser, fernet_key: bytes):
        self.root = tk.Tk()
        self.root.title("Gestor de Contraseñas - Panel Principal")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Datos de sesión
        self.admin_user = admin_user
        self.fernet_key = fernet_key
        self.session_manager = SessionManager()
        self.session_manager.start_session(admin_user, fernet_key)
        
        # Gestor de cuentas
        self.account_manager = AccountManager(fernet_key)
        
        # Variables de control
        self.selected_account = None
        self.show_passwords = tk.BooleanVar(value=False)
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz
        self.create_widgets()
        
        # Cargar cuentas
        self.refresh_accounts_list()
        
        # Verificar sesión periódicamente
        self.check_session()
    
    def setup_styles(self):
        """Configura los estilos de la aplicación"""
        self.root.configure(bg='#1e1e1e')
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores generales
        style.configure('.',
                        background='#1e1e1e',
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none')
        
        # Treeview
        style.configure('Treeview',
                        background='#2d2d2d',
                        foreground='white',
                        rowheight=25,
                        fieldbackground='#2d2d2d',
                        borderwidth=0)
        style.map('Treeview',
                background=[('selected', '#0d7377')])
        
        # Headers
        style.configure('Treeview.Heading',
                background='#252525',
                foreground='white',
                    relief='flat')
        
        # Labels
        style.configure('Title.TLabel',
            font=('Arial', 14, 'bold'))
        style.configure('Subtitle.TLabel',
            font=('Arial', 11))
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame superior (header)
        self.create_header()
        
        # Frame principal con dos paneles
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Panel izquierdo (lista de cuentas)
        self.create_left_panel(main_container)
        
        # Panel derecho (detalles y acciones)
        self.create_right_panel(main_container)
        
        # Barra de estado
        self.create_status_bar()
    
    def create_header(self):
        """Crea el header de la aplicación"""
        header_frame = tk.Frame(self.root, bg='#0d7377', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Contenedor interno
        inner_header = tk.Frame(header_frame, bg='#0d7377')
        inner_header.pack(expand=True, fill='both', padx=20)
        
        # Título y usuario
        left_frame = tk.Frame(inner_header, bg='#0d7377')
        left_frame.pack(side='left', fill='y')
        
        tk.Label(left_frame,
                text="🔐 Gestor de Contraseñas",
                bg='#0d7377',
                fg='white',
                font=('Arial', 16, 'bold')).pack(side='left', pady=15)
        
        # Info de usuario y botón de logout
        right_frame = tk.Frame(inner_header, bg='#0d7377')
        right_frame.pack(side='right', fill='y')
        
        user_info = tk.Frame(right_frame, bg='#0d7377')
        user_info.pack(side='left', padx=20, pady=15)
        
        tk.Label(user_info,
                text=f"👤 {self.admin_user.username}",
                bg='#0d7377',
                fg='white',
                font=('Arial', 11)).pack()
        
        logout_btn = tk.Button(right_frame,
                            text="Cerrar Sesión",
                            command=self.logout,
                            bg='#d32f2f',
                            fg='white',
                            font=('Arial', 10),
                            padx=15,
                            pady=5,
                            cursor='hand2',
                            relief='flat')
        logout_btn.pack(side='right', pady=15)
    
    def create_left_panel(self, parent):
        """Crea el panel izquierdo con la lista de cuentas"""
        left_frame = tk.Frame(parent, bg='#252525', width=400)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Título y controles
        controls_frame = tk.Frame(left_frame, bg='#252525')
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(controls_frame,
                text="Cuentas Guardadas",
                style='Title.TLabel').pack(side='left')
        
        # Botón agregar
        add_btn = tk.Button(controls_frame,
                        text="+ Nueva",
                        command=self.show_add_account_dialog,
                        bg='#14ae5c',
                        fg='white',
                        font=('Arial', 10),
                        padx=15,
                        pady=5,
                        cursor='hand2',
                        relief='flat')
        add_btn.pack(side='right')
        
        # Búsqueda
        search_frame = tk.Frame(left_frame, bg='#252525')
        search_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_accounts())
        
        search_entry = ttk.Entry(search_frame,
                                textvariable=self.search_var,
                                font=('Arial', 11))
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Filtro por categoría
        self.category_var = tk.StringVar(value="Todas")
        categories = ["Todas"] + self.account_manager.get_all_categories()
        
        category_combo = ttk.Combobox(search_frame,
                                    textvariable=self.category_var,
                                    values=categories,
                                    state='readonly',
                                    width=15)
        category_combo.pack(side='right')
        category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_accounts())
        
        # Lista de cuentas (Treeview)
        tree_frame = tk.Frame(left_frame, bg='#252525')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        self.accounts_tree = ttk.Treeview(tree_frame,
                                columns=( 'Usuario', 'Categoría'),
                                show='tree headings',
                                yscrollcommand=scrollbar.set)
        self.accounts_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.accounts_tree.yview)
        
        # Configurar columnas
        self.accounts_tree.heading('#0', text='Plataforma')
        self.accounts_tree.heading('Usuario', text='Usuario/Email')
        self.accounts_tree.heading('Categoría', text='Categoría')
        
        self.accounts_tree.column('#0', width=150)
        self.accounts_tree.column('Usuario', width=150)
        self.accounts_tree.column('Categoría', width=100)
        
        # Bind eventos
        self.accounts_tree.bind('<<TreeviewSelect>>', self.on_account_select)
        self.accounts_tree.bind('<Double-Button-1>', lambda e: self.show_password())
    
    def create_right_panel(self, parent):
        """Crea el panel derecho con detalles y acciones"""
        right_frame = tk.Frame(parent, bg='#252525', width=350)
        right_frame.pack(side='right', fill='both', padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Título
        ttk.Label(right_frame,
                 text="Detalles de la Cuenta",
                 style='Title.TLabel').pack(padx=20, pady=(20, 10))
        
        # Frame de detalles
        self.details_frame = tk.Frame(right_frame, bg='#252525')
        self.details_frame.pack(fill='both', expand=True, padx=20)
        
        # Mensaje cuando no hay cuenta seleccionada
        self.no_selection_label = ttk.Label(self.details_frame,
                                           text="Seleccione una cuenta\npara ver los detalles",
                                           style='Subtitle.TLabel',
                                           justify='center')
        self.no_selection_label.pack(expand=True)
        
        # Frame de detalles (inicialmente oculto)
        self.account_details_frame = tk.Frame(self.details_frame, bg='#252525')
        
        # Acciones
        actions_frame = tk.Frame(right_frame, bg='#252525')
        actions_frame.pack(fill='x', padx=20, pady=20)
        
        # Botones de acción
        self.edit_btn = tk.Button(actions_frame,
                                 text="✏️ Editar",
                                 command=self.edit_account,
                                 bg='#1976d2',
                                 fg='white',
                                 font=('Arial', 10),
                                 padx=15,
                                 pady=8,
                                 cursor='hand2',
                                 relief='flat',
                                 state='disabled')
        self.edit_btn.pack(side='left', padx=(0, 10))
        
        self.delete_btn = tk.Button(actions_frame,
                                   text="🗑️ Eliminar",
                                   command=self.delete_account,
                                   bg='#d32f2f',
                                   fg='white',
                                   font=('Arial', 10),
                                   padx=15,
                                   pady=8,
                                   cursor='hand2',
                                   relief='flat',
                                   state='disabled')
        self.delete_btn.pack(side='left')
        
        # Botón generar contraseña
        gen_pass_btn = tk.Button(actions_frame,
                                text="🔐 Generar Contraseña",
                                command=self.generate_password,
                                bg='#673ab7',
                                fg='white',
                                font=('Arial', 10),
                                padx=15,
                                pady=8,
                                cursor='hand2',
                                relief='flat')
        gen_pass_btn.pack(side='right')
    
    def create_status_bar(self):
        """Crea la barra de estado"""
        status_frame = tk.Frame(self.root, bg='#1a1a1a', height=30)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)
        
        # Información de cuentas
        self.status_label = tk.Label(status_frame,
                                    text="",
                                    bg='#1a1a1a',
                                    fg='#888',
                                    font=('Arial', 9))
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Hora
        self.time_label = tk.Label(status_frame,
                                  text="",
                                  bg='#1a1a1a',
                                  fg='#888',
                                  font=('Arial', 9))
        self.time_label.pack(side='right', padx=10, pady=5)
        
        self.update_status_bar()
        self.update_time()
    
    def refresh_accounts_list(self):
        """Actualiza la lista de cuentas"""
        # Limpiar árbol
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Actualizar combo de categorías
        categories = ["Todas"] + self.account_manager.get_all_categories()
        if hasattr(self, 'category_var'):
            category_combo = self.root.nametowidget(self.accounts_tree.master.master.winfo_children()[1].winfo_children()[1])
            category_combo['values'] = categories
        
        # Agregar cuentas
        self.filter_accounts()
        
        # Actualizar barra de estado
        self.update_status_bar()
    
    def filter_accounts(self):
        """Filtra las cuentas según búsqueda y categoría"""
        # Limpiar árbol
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Obtener cuentas filtradas del manager
        accounts = self.account_manager.get_filtered_accounts(
            search=self.search_var.get(),
            category=self.category_var.get()
        )
        
        # Agregar al árbol
        for account in accounts:
            self.accounts_tree.insert('', 'end',
                                     iid=account.id,
                                     text=account.platform,
                                     values=(account.email_or_username, account.category))
    
    def on_account_select(self, event):
        """Maneja la selección de una cuenta"""
        selection = self.accounts_tree.selection()
        if not selection:
            return
        
        # Obtener cuenta seleccionada
        account_id = selection[0]
        self.selected_account = self.account_manager.get_account_byID(account_id)
        
        if self.selected_account:
            self.show_account_details()
            self.edit_btn.config(state='normal')
            self.delete_btn.config(state='normal')

    def show_account_details(self):
        """Muestra los detalles de la cuenta seleccionada"""
        # Ocultar mensaje de no selección
        self.no_selection_label.pack_forget()
        
        # Limpiar frame de detalles
        for widget in self.account_details_frame.winfo_children():
            widget.destroy()
        
        self.account_details_frame.pack(fill='both', expand=True)
        
        # Detalles
        details = [
            ("Plataforma:", self.selected_account.platform),
            ("Usuario/Email:", self.selected_account.email_or_username),
            ("Categoría:", self.selected_account.category),
            ("Contraseña:", "*" * 12),
        ]
        
        for label, value in details:
            row_frame = tk.Frame(self.account_details_frame, bg='#252525')
            row_frame.pack(fill='x', pady=5)
            
            tk.Label(row_frame,
                    text=label,
                    bg='#252525',
                    fg='#888',
                    font=('Arial', 10),
                    width=15,
                    anchor='w').pack(side='left')
            
            if label == "Contraseña:":
                self.password_label = tk.Label(row_frame,
                                             text=value,
                                             bg='#252525',
                                             fg='white',
                                             font=('Arial', 10, 'bold'))
                self.password_label.pack(side='left', padx=(0, 10))
                
                show_btn = tk.Button(row_frame,
                                   text="👁️",
                                   command=self.toggle_password,
                                   bg='#252525',
                                   fg='white',
                                   font=('Arial', 8),
                                   cursor='hand2',
                                   relief='flat')
                show_btn.pack(side='left')
            else:
                tk.Label(row_frame,
                        text=value,
                        bg='#252525',
                        fg='white',
                        font=('Arial', 10, 'bold')).pack(side='left')
        
        # Notas
        if self.selected_account.notes:
            notes_frame = tk.Frame(self.account_details_frame, bg='#252525')
            notes_frame.pack(fill='x', pady=(15, 5))
            
            tk.Label(notes_frame,
                    text="Notas:",
                    bg='#252525',
                    fg='#888',
                    font=('Arial', 10),
                    anchor='w').pack(anchor='w')
            
            notes_text = tk.Text(notes_frame,
                               bg='#2d2d2d',
                               fg='white',
                               font=('Arial', 9),
                               height=4,
                               wrap='word',
                               relief='flat')
            notes_text.pack(fill='x', pady=5)
            notes_text.insert('1.0', self.selected_account.notes)
            notes_text.config(state='disabled')
        
        # Fechas
        if self.selected_account.created_at:
            dates_frame = tk.Frame(self.account_details_frame, bg='#252525')
            dates_frame.pack(fill='x', pady=(15, 0))
            
            tk.Label(dates_frame,
                    text=f"Creada: {self.selected_account.created_at[:10]}",
                    bg='#252525',
                    fg='#666',
                    font=('Arial', 8)).pack(anchor='w')
            
            if self.selected_account.updated_at:
                tk.Label(dates_frame,
                        text=f"Actualizada: {self.selected_account.updated_at[:10]}",
                        bg='#252525',
                        fg='#666',
                        font=('Arial', 8)).pack(anchor='w')
    
    def toggle_password(self):
        """Alterna la visibilidad de la contraseña"""
        if self.password_label.cget('text').startswith('*'):
            password = self.account_manager.get_decrypted_password(self.selected_account.id)
            self.password_label.config(text=password)
        else:
            self.password_label.config(text='*' * 12)
    
    def show_password(self):
        """Muestra la contraseña en un diálogo"""
        if not self.selected_account:
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Contraseña")
        dialog.geometry("400x200")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Contenido
        tk.Label(dialog,
                text=f"Contraseña de {self.selected_account.platform}",
                bg='#1e1e1e',
                fg='white',
                font=('Arial', 12, 'bold')).pack(pady=20)
        
        # Frame para contraseña
        pass_frame = tk.Frame(dialog, bg='#2d2d2d', relief='solid', bd=1)
        pass_frame.pack(padx=20, pady=10)
        
        password = self.account_manager.get_decrypted_password(self.selected_account.id)
        password_text = tk.Text(pass_frame,
                               bg='#2d2d2d',
                               fg='white',
                               font=('Consolas', 14),
                               height=1,
                               width=30,
                               relief='flat')
        password_text.pack(padx=10, pady=10)
        password_text.insert('1.0', password)
        password_text.config(state='disabled')
        
        # Botón copiar
        def copy_password():
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            messagebox.showinfo("Copiado", "Contraseña copiada al portapapeles", parent=dialog)
            dialog.destroy()
        
        tk.Button(dialog,
                 text="📋 Copiar",
                 command=copy_password,
                 bg='#0d7377',
                 fg='white',
                 font=('Arial', 10),
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(pady=10)
    
    def show_add_account_dialog(self):
        """Muestra el diálogo para agregar una cuenta"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Nueva Cuenta")
        dialog.geometry("500x550")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Título
        tk.Label(main_frame,
                text="Nueva Cuenta",
                bg='#1e1e1e',
                fg='white',
                font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Campos
        fields = []
        
        # Plataforma
        tk.Label(main_frame, text="Plataforma:", bg='#1e1e1e', fg='white', 
                font=('Arial', 11)).pack(anchor='w', pady=(10, 5))
        platform_entry = ttk.Entry(main_frame, font=('Arial', 11), width=40)
        platform_entry.pack(fill='x')
        fields.append(platform_entry)
        
        # Usuario/Email
        tk.Label(main_frame, text="Usuario/Email:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        user_entry = ttk.Entry(main_frame, font=('Arial', 11), width=40)
        user_entry.pack(fill='x')
        fields.append(user_entry)
        
        # Contraseña
        tk.Label(main_frame, text="Contraseña:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        
        pass_frame = tk.Frame(main_frame, bg='#1e1e1e')
        pass_frame.pack(fill='x')
        
        password_entry = ttk.Entry(pass_frame, font=('Arial', 11), width=30)
        password_entry.pack(side='left', fill='x', expand=True)
        fields.append(password_entry)
        
        # Botón generar
        def generate_for_field():
            password = self.account_manager.suggest_strong_password(16)
            password_entry.delete(0, tk.END)
            password_entry.insert(0, password)
        
        tk.Button(pass_frame,
                 text="Generar",
                 command=generate_for_field,
                 bg='#673ab7',
                 fg='white',
                 font=('Arial', 9),
                 padx=10,
                 pady=5,
                 cursor='hand2',
                 relief='flat').pack(side='right', padx=(10, 0))
        
        # Categoría
        tk.Label(main_frame, text="Categoría:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        
        categories = ["videojuegos", "correo", "streaming", "productividad", "otros"]
        category_var = tk.StringVar(value=categories[0])
        
        category_frame = tk.Frame(main_frame, bg='#1e1e1e')
        category_frame.pack(fill='x')
        
        for cat in categories:
            tk.Radiobutton(category_frame,
                          text=cat.capitalize(),
                          variable=category_var,
                          value=cat,
                          bg='#1e1e1e',
                          fg='white',
                          selectcolor='#0d7377',
                          font=('Arial', 10)).pack(side='left', padx=(0, 15))
        
        # Notas
        tk.Label(main_frame, text="Notas (opcional):", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        notes_text = tk.Text(main_frame, 
                           bg='#2d2d2d',
                           fg='white',
                           font=('Arial', 10),
                           height=4,
                           relief='flat')
        notes_text.pack(fill='x')
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='#1e1e1e')
        buttons_frame.pack(fill='x', pady=(30, 0))
        
        def save_account():
            platform = platform_entry.get().strip()
            user = user_entry.get().strip()
            password = password_entry.get().strip()
            category = category_var.get()
            notes = notes_text.get('1.0', 'end-1c').strip()
            
            if not all([platform, user, password]):
                messagebox.showerror("Error", "Complete todos los campos obligatorios", parent=dialog)
                return
            
            try:
                self.account_manager.create_account(
                    platform=platform,
                    email_or_username=user,
                    password=password,
                    category=category,
                    notes=notes
                )
                messagebox.showinfo("Éxito", f"Cuenta '{platform}' agregada correctamente", parent=dialog)
                self.refresh_accounts_list()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}", parent=dialog)
        
        tk.Button(buttons_frame,
                 text="Guardar",
                 command=save_account,
                 bg='#14ae5c',
                 fg='white',
                 font=('Arial', 11, 'bold'),
                 padx=30,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(side='left', padx=(0, 10))
        
        tk.Button(buttons_frame,
                 text="Cancelar",
                 command=dialog.destroy,
                 bg='#555',
                 fg='white',
                 font=('Arial', 11),
                 padx=30,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(side='left')
    
    def edit_account(self):
        """Edita la cuenta seleccionada"""
        if not self.selected_account:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Cuenta")
        dialog.geometry("500x550")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Título
        tk.Label(main_frame,
                text=f"Editar: {self.selected_account.platform}",
                bg='#1e1e1e',
                fg='white',
                font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Usuario/Email
        tk.Label(main_frame, text="Usuario/Email:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        user_entry = ttk.Entry(main_frame, font=('Arial', 11), width=40)
        user_entry.pack(fill='x')
        user_entry.insert(0, self.selected_account.email_or_username)
        
        # Contraseña
        tk.Label(main_frame, text="Contraseña:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        
        pass_frame = tk.Frame(main_frame, bg='#1e1e1e')
        pass_frame.pack(fill='x')
        
        password_entry = ttk.Entry(pass_frame, font=('Arial', 11), width=30)
        password_entry.pack(side='left', fill='x', expand=True)
        password_entry.insert(0, self.account_manager.get_decrypted_password(self.selected_account.id))
        
        # Botón generar
        def generate_for_field():
            password = self.account_manager.suggest_strong_password(16)
            password_entry.delete(0, tk.END)
            password_entry.insert(0, password)
        
        tk.Button(pass_frame,
                 text="Generar",
                 command=generate_for_field,
                 bg='#673ab7',
                 fg='white',
                 font=('Arial', 9),
                 padx=10,
                 pady=5,
                 cursor='hand2',
                 relief='flat').pack(side='right', padx=(10, 0))
        
        # Categoría
        tk.Label(main_frame, text="Categoría:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        
        categories = ["videojuegos", "correo", "streaming", "productividad", "otros"]
        category_var = tk.StringVar(value=self.selected_account.category)
        
        category_combo = ttk.Combobox(main_frame,
                                     textvariable=category_var,
                                     values=categories,
                                     state='readonly',
                                     font=('Arial', 11))
        category_combo.pack(fill='x')
        
        # Notas
        tk.Label(main_frame, text="Notas:", bg='#1e1e1e', fg='white',
                font=('Arial', 11)).pack(anchor='w', pady=(15, 5))
        notes_text = tk.Text(main_frame,
                           bg='#2d2d2d',
                           fg='white',
                           font=('Arial', 10),
                           height=4,
                           relief='flat')
        notes_text.pack(fill='x')
        if self.selected_account.notes:
            notes_text.insert('1.0', self.selected_account.notes)
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='#1e1e1e')
        buttons_frame.pack(fill='x', pady=(30, 0))
        
        def update_account():
            user = user_entry.get().strip()
            password = password_entry.get().strip()
            category = category_var.get()
            notes = notes_text.get('1.0', 'end-1c').strip()
            
            if not all([user, password]):
                messagebox.showerror("Error", "Usuario y contraseña son obligatorios", parent=dialog)
                return
            
            try:
                self.account_manager.update_account(
                    self.selected_account.id,
                    email_or_username=user,
                    password=password,
                    category=category,
                    notes=notes
                )
                messagebox.showinfo("Éxito", "Cuenta actualizada correctamente", parent=dialog)
                self.refresh_accounts_list()
                self.show_account_details()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar: {str(e)}", parent=dialog)
        
        tk.Button(buttons_frame,
                 text="Actualizar",
                 command=update_account,
                 bg='#1976d2',
                 fg='white',
                 font=('Arial', 11, 'bold'),
                 padx=30,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(side='left', padx=(0, 10))
        
        tk.Button(buttons_frame,
                 text="Cancelar",
                 command=dialog.destroy,
                 bg='#555',
                 fg='white',
                 font=('Arial', 11),
                 padx=30,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(side='left')
    
    def delete_account(self):
        """Elimina la cuenta seleccionada"""
        if not self.selected_account:
            return
        
        result = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de eliminar la cuenta '{self.selected_account.platform}'?\n\nEsta acción no se puede deshacer."
        )
        
        if result:
            try:
                self.account_manager.delete_account(self.selected_account.id)
                messagebox.showinfo("Éxito", "Cuenta eliminada correctamente")
                self.selected_account = None
                self.refresh_accounts_list()
                
                # Limpiar panel derecho
                self.account_details_frame.pack_forget()
                self.no_selection_label.pack(expand=True)
                self.edit_btn.config(state='disabled')
                self.delete_btn.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar: {str(e)}")
    
    def generate_password(self):
        """Muestra diálogo para generar contraseña"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Generador de Contraseñas")
        dialog.geometry("450x350")
        dialog.configure(bg='#1e1e1e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Título
        tk.Label(main_frame,
                text="Generador de Contraseñas",
                bg='#1e1e1e',
                fg='white',
                font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Longitud
        length_frame = tk.Frame(main_frame, bg='#1e1e1e')
        length_frame.pack(fill='x', pady=10)
        
        tk.Label(length_frame,
                text="Longitud:",
                bg='#1e1e1e',
                fg='white',
                font=('Arial', 11)).pack(side='left', padx=(0, 10))
        
        length_var = tk.IntVar(value=16)
        length_spinbox = ttk.Spinbox(length_frame,
                                    from_=8,
                                    to=32,
                                    textvariable=length_var,
                                    width=10,
                                    font=('Arial', 11))
        length_spinbox.pack(side='left')
        
        # Resultado
        result_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='solid', bd=1)
        result_frame.pack(fill='x', pady=20)
        
        result_text = tk.Text(result_frame,
                            bg='#2d2d2d',
                            fg='white',
                            font=('Consolas', 12),
                            height=3,
                            wrap='word',
                            relief='flat')
        result_text.pack(padx=10, pady=10)
        
        # Botones
        buttons_frame = tk.Frame(main_frame, bg='#1e1e1e')
        buttons_frame.pack(fill='x')
        
        def generate():
            password = self.account_manager.suggest_strong_password(length_var.get())
            result_text.delete('1.0', tk.END)
            result_text.insert('1.0', password)
        
        def copy():
            password = result_text.get('1.0', 'end-1c')
            if password:
                self.root.clipboard_clear()
                self.root.clipboard_append(password)
                messagebox.showinfo("Copiado", "Contraseña copiada al portapapeles", parent=dialog)
        
        tk.Button(buttons_frame,
                 text="Generar",
                 command=generate,
                 bg='#673ab7',
                 fg='white',
                 font=('Arial', 11, 'bold'),
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(side='left', padx=(0, 10))
        
        tk.Button(buttons_frame,
                 text="Copiar",
                 command=copy,
                 bg='#0d7377',
                 fg='white',
                 font=('Arial', 11),
                 padx=20,
                 pady=8,
                 cursor='hand2',
                 relief='flat').pack(side='left')
        
        # Generar inicial
        generate()
    
    def update_status_bar(self):
        """Actualiza la barra de estado"""
        summary = self.account_manager.get_accounts_summary()
        total = summary['total']
        
        status_text = f"Total de cuentas: {total}"
        if summary['by_category']:
            categories_text = " | ".join([f"{cat}: {count}" 
                                        for cat, count in summary['by_category'].items()])
            status_text += f" | {categories_text}"
        
        self.status_label.config(text=status_text)
    
    def update_time(self):
        """Actualiza la hora en la barra de estado"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def check_session(self):
        """Verifica si la sesión sigue siendo válida"""
        if not self.session_manager.is_session_valid():
            messagebox.showwarning("Sesión expirada", 
                                 "Su sesión ha expirado. Por favor, inicie sesión nuevamente.")
            self.logout()
        else:
            # Verificar cada minuto
            self.root.after(60000, self.check_session)
    
    def logout(self):
        """Cierra la sesión y vuelve al login"""
        self.session_manager.end_session()
        self.root.destroy()
        
        # Volver a mostrar login
        from Vista.login import start_login
        start_login(lambda u, k: HomeWindow(u, k).run())
    
    def run(self):
        """Ejecuta la ventana principal"""
        self.root.mainloop()
