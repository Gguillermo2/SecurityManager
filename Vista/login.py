# Vista/login.py
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.autenticacion import autenticar_admin, verificar_2fa, obtener_codigo_2fa, generar_Admin
from core.almacenamiento import load_json_data

# Función helper para iniciar el login
def start_login(on_success_callback):
    """
    Inicia la ventana de login
    on_success_callback: función que se llama cuando el login es exitoso
                        recibe (admin_user, fernet_key)
    """
    login = LoginWindow(on_success_callback)
    login.run()

class LoginWindow:
    def __init__(self, on_success_callback):
        self.root = tk.Tk()
        self.root.title("Gestor de Contraseñas - Login")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # Callback cuando el login es exitoso
        self.on_success = on_success_callback
        self.current_user = None
        self.fernet_key = None
        
        # Configurar estilo
        self.setup_styles()
        
        # Verificar si existe usuario admin
        if not self.check_admin_exists():
            self.show_create_admin_screen()
        else:
            self.show_login_screen()
    
    def setup_styles(self):
        """Configura los estilos de la aplicación"""
        self.root.configure(bg='#1e1e1e')
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Title.TLabel', 
                       background='#1e1e1e', 
                       foreground='white',
                       font=('Arial', 16, 'bold'))
        style.configure('Regular.TLabel',
                       background='#1e1e1e',
                       foreground='white',
                       font=('Arial', 10))
    
    def check_admin_exists(self):
        """Verifica si existe un usuario administrador"""
        return load_json_data("DBusers.json") is not None
    
    def clear_window(self):
        """Limpia todos los widgets de la ventana"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_create_admin_screen(self):
        """Muestra la pantalla de creación de admin"""
        self.clear_window()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Título
        title = ttk.Label(main_frame, text="Crear Usuario Administrador", 
                         style='Title.TLabel')
        title.pack(pady=(0, 30))
        
        # Username
        ttk.Label(main_frame, text="Nombre de usuario:", 
                 style='Regular.TLabel').pack(anchor='w', pady=(10, 5))
        self.username_entry = ttk.Entry(main_frame, width=30, font=('Arial', 11))
        self.username_entry.pack(fill='x')
        
        # Contraseña maestra
        ttk.Label(main_frame, text="Contraseña maestra:", 
                 style='Regular.TLabel').pack(anchor='w', pady=(15, 5))
        self.password_entry = ttk.Entry(main_frame, width=30, show="*", font=('Arial', 11))
        self.password_entry.pack(fill='x')
        
        # Contraseña 2FA
        ttk.Label(main_frame, text="Contraseña para 2FA:", 
                 style='Regular.TLabel').pack(anchor='w', pady=(15, 5))
        self.password_2fa_entry = ttk.Entry(main_frame, width=30, show="*", font=('Arial', 11))
        self.password_2fa_entry.pack(fill='x')
        
        # Botón crear
        create_btn = tk.Button(main_frame, 
                              text="Crear Usuario",
                              command=self.create_admin,
                              bg='#0d7377',
                              fg='white',
                              font=('Arial', 12, 'bold'),
                              padx=20,
                              pady=10,
                              cursor='hand2',
                              relief='flat')
        create_btn.pack(pady=30)
    
    def create_admin(self):
        """Crea el usuario administrador"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        password_2fa = self.password_2fa_entry.get()
        
        if not all([username, password, password_2fa]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return
        
        # Simular la entrada para generar_Admin
        import io
        import contextlib
        from unittest.mock import patch
        
        # Guardar directamente sin usar input/getpass
        from core.seguridad import hash_password_bcrypt, generate_salt
        from Modelo.models import AdminUser
        from core.almacenamiento import save_jsonD
        from base64 import urlsafe_b64encode
        
        try:
            # Hash de contraseñas
            hashed_password = hash_password_bcrypt(password)
            hashed_password_2fa = hash_password_bcrypt(password_2fa)
            
            # Generar salt para Fernet
            fernet_salt_bytes = generate_salt()
            fernet_salt_str = urlsafe_b64encode(fernet_salt_bytes).decode('utf-8')
            
            # Crear usuario
            nuevo_admin = AdminUser(
                username=username,
                password=hashed_password,
                password_2fa=hashed_password_2fa,
                fernet_key_salt=fernet_salt_str
            )
            
            # Guardar
            save_jsonD("DBusers.json", nuevo_admin.model_dump())
            
            messagebox.showinfo("Éxito", "Usuario administrador creado correctamente")
            self.show_login_screen()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear usuario: {str(e)}")
    
    def show_login_screen(self):
        """Muestra la pantalla de login"""
        self.clear_window()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Logo/Título
        title_frame = tk.Frame(main_frame, bg='#1e1e1e')
        title_frame.pack(pady=(0, 30))
        
        tk.Label(title_frame, text="🔐", font=('Arial', 48), bg='#1e1e1e').pack()
        ttk.Label(title_frame, text="Gestor de Contraseñas", 
                 style='Title.TLabel').pack()
        
        # Frame de login
        login_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='flat')
        login_frame.pack(fill='both', padx=20, pady=20)
        
        inner_frame = tk.Frame(login_frame, bg='#2d2d2d')
        inner_frame.pack(padx=30, pady=30)
        
        # Username
        ttk.Label(inner_frame, text="Usuario:", 
                 font=('Arial', 11), background='#2d2d2d',
                 foreground='white').grid(row=0, column=0, sticky='w', pady=10)
        self.username_entry = ttk.Entry(inner_frame, width=25, font=('Arial', 11))
        self.username_entry.grid(row=0, column=1, padx=(10, 0))
        
        # Password
        ttk.Label(inner_frame, text="Contraseña:", 
                 font=('Arial', 11), background='#2d2d2d',
                 foreground='white').grid(row=1, column=0, sticky='w', pady=10)
        self.password_entry = ttk.Entry(inner_frame, width=25, show="*", font=('Arial', 11))
        self.password_entry.grid(row=1, column=1, padx=(10, 0))
        
        # Botón de login
        login_btn = tk.Button(main_frame,
                            text="Iniciar Sesión",
                            command=self.attempt_login,
                            bg='#0d7377',
                            fg='white',
                            font=('Arial', 12, 'bold'),
                            padx=30,
                            pady=10,
                            cursor='hand2',
                            relief='flat')
        login_btn.pack(pady=20)
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.attempt_login())
    
    def attempt_login(self):
        """Intenta hacer login con las credenciales"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor complete todos los campos")
            return
        
        # Simular entrada para autenticar_admin
        from unittest.mock import patch
        
        with patch('builtins.input', side_effect=[username]):
            with patch('getpass.getpass', return_value=password):
                admin_user, fernet_key = autenticar_admin()
        
        if admin_user and fernet_key:
            self.current_user = admin_user
            self.fernet_key = fernet_key
            self.show_2fa_screen()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    
    def show_2fa_screen(self):
        """Muestra la pantalla de 2FA"""
        self.clear_window()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Título
        title = ttk.Label(main_frame, text="Verificación de Dos Factores", 
                         style='Title.TLabel')
        title.pack(pady=(0, 30))
        
        # Instrucciones
        info_label = ttk.Label(main_frame, 
                              text="Ingrese su contraseña de 2FA para generar el código",
                              style='Regular.TLabel')
        info_label.pack(pady=(0, 20))
        
        # Contraseña 2FA
        self.password_2fa_entry = ttk.Entry(main_frame, width=30, show="*", font=('Arial', 11))
        self.password_2fa_entry.pack(pady=10)
        
        # Botón verificar
        verify_btn = tk.Button(main_frame,
                              text="Verificar y Generar Código",
                              command=self.verify_2fa,
                              bg='#0d7377',
                              fg='white',
                              font=('Arial', 11, 'bold'),
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              relief='flat')
        verify_btn.pack(pady=20)
        
        # Frame para el código (inicialmente oculto)
        self.code_frame = tk.Frame(main_frame, bg='#1e1e1e')
        self.code_frame.pack(pady=20)
    
    def verify_2fa(self):
        """Verifica la contraseña 2FA y muestra el código"""
        password_2fa = self.password_2fa_entry.get()
        
        if not password_2fa:
            messagebox.showerror("Error", "Por favor ingrese la contraseña 2FA")
            return
        
        # Verificar contraseña 2FA
        from unittest.mock import patch
        
        with patch('getpass.getpass', return_value=password_2fa):
            if verificar_2fa(self.current_user):
                # Generar y mostrar código
                code = obtener_codigo_2fa()
                self.show_code_input(code)
            else:
                messagebox.showerror("Error", "Contraseña 2FA incorrecta")
    
    def show_code_input(self, generated_code):
        """Muestra el campo para ingresar el código"""
        # Limpiar frame de código
        for widget in self.code_frame.winfo_children():
            widget.destroy()
        
        # Mostrar código generado
        code_display = tk.Frame(self.code_frame, bg='#0d7377', relief='solid', bd=2)
        code_display.pack(pady=10)
        
        tk.Label(code_display, 
                text=f"Código: {generated_code}",
                bg='#0d7377',
                fg='white',
                font=('Arial', 16, 'bold'),
                padx=20,
                pady=10).pack()
        
        # Campo para ingresar código
        ttk.Label(self.code_frame, 
                 text="Ingrese el código mostrado:",
                 style='Regular.TLabel').pack(pady=(20, 5))
        
        self.code_entry = ttk.Entry(self.code_frame, width=20, font=('Arial', 14))
        self.code_entry.pack(pady=5)
        self.code_entry.focus()
        
        # Botón confirmar
        confirm_btn = tk.Button(self.code_frame,
                               text="Confirmar",
                               command=lambda: self.confirm_code(generated_code),
                               bg='#14ae5c',
                               fg='white',
                               font=('Arial', 11, 'bold'),
                               padx=30,
                               pady=8,
                               cursor='hand2',
                               relief='flat')
        confirm_btn.pack(pady=15)
        
        # Bind Enter
        self.code_entry.bind('<Return>', lambda e: self.confirm_code(generated_code))
    
    def confirm_code(self, correct_code):
        """Confirma el código ingresado"""
        entered_code = self.code_entry.get()
        
        if entered_code == correct_code:
            messagebox.showinfo("Éxito", "¡Autenticación completa!")
            self.root.destroy()
            # Llamar al callback con los datos de sesión
            self.on_success(self.current_user, self.fernet_key)
        else:
            messagebox.showerror("Error", "Código incorrecto")
            self.code_entry.delete(0, tk.END)
            self.code_entry.focus()
    
    def run(self):
        """Ejecuta la ventana de login"""
        self.root.mainloop()


