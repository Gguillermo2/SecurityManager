# Vista/login.py
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.autenticacion import admin_exists, create_admin as create_admin_user, authenticate_admin, validate_totp

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
        self.root.geometry("600x700")
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
        return admin_exists()

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

        if not all([username, password]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        try:
            nuevo_admin, totp_secret = create_admin_user(username, password)
            self.current_user = nuevo_admin
            self.fernet_key = None
            self.show_totp_qr(username, totp_secret)

        except Exception as e:
            messagebox.showerror("Error", f"Error al crear usuario: {str(e)}")
    
    def show_totp_qr(self, username, totp_secret):
        """Muestra el QR para configurar TOTP"""
        import qrcode
        import pyotp
        from PIL import Image, ImageTk
        import io
        
        self.clear_window()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Título
        ttk.Label(main_frame, text="Configurar Autenticación TOTP", 
                 style='Title.TLabel').pack(pady=(0, 20))
        
        # Instrucciones
        ttk.Label(main_frame, 
                 text="Escanee este código QR con su aplicación de autenticación\n(Google Authenticator, Authy, etc.)",
                 style='Regular.TLabel',
                 justify='center').pack(pady=(0, 20))
        
        # Generar QR
        totp = pyotp.TOTP(totp_secret)
        uri = totp.provisioning_uri(name=username, issuer_name="GestorWroser")
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a PhotoImage
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        img_tk = ImageTk.PhotoImage(Image.open(bio))
        
        # Mostrar QR
        qr_label = tk.Label(main_frame, image=img_tk, bg='#1e1e1e')
        qr_label.image = img_tk  # Mantener referencia
        qr_label.pack(pady=20)
        
        # Secreto como texto alternativo
        ttk.Label(main_frame, 
                 text=f"Si no puede escanear, ingrese manualmente:\n{totp_secret}",
                 style='Regular.TLabel',
                 justify='center').pack(pady=(0, 20))
        
        # Botón continuar
        continue_btn = tk.Button(main_frame,
                                text="Continuar al Login",
                                command=self.show_login_screen,
                                bg='#0d7377',
                                fg='white',
                                font=('Arial', 12, 'bold'),
                                padx=20,
                                pady=10,
                                cursor='hand2',
                                relief='flat')
        continue_btn.pack(pady=20)
    
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

        admin_user, fernet_key = authenticate_admin(username, password)

        if admin_user and fernet_key:
            self.current_user = admin_user
            self.fernet_key = fernet_key
            self.show_totp_screen()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    
    def show_totp_screen(self):
        """Muestra la pantalla de verificación TOTP"""
        self.clear_window()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)
        
        # Título
        title = ttk.Label(main_frame, text="Verificación TOTP", 
                         style='Title.TLabel')
        title.pack(pady=(0, 30))
        
        # Instrucciones
        info_label = ttk.Label(main_frame, 
                              text="Ingrese el código de 6 dígitos de su aplicación de autenticación",
                              style='Regular.TLabel')
        info_label.pack(pady=(0, 20))
        
        # Campo para código TOTP
        self.totp_entry = ttk.Entry(main_frame, width=20, font=('Arial', 18), justify='center')
        self.totp_entry.pack(pady=10)
        self.totp_entry.focus()
        
        # Botón verificar
        verify_btn = tk.Button(main_frame,
                              text="Verificar",
                              command=self.verify_totp,
                              bg='#0d7377',
                              fg='white',
                              font=('Arial', 12, 'bold'),
                              padx=30,
                              pady=10,
                              cursor='hand2',
                              relief='flat')
        verify_btn.pack(pady=20)
        
        # Bind Enter
        self.totp_entry.bind('<Return>', lambda e: self.verify_totp())
    
    def verify_totp(self):
        """Verifica el código TOTP"""
        entered_code = self.totp_entry.get().strip()

        if not entered_code:
            messagebox.showerror("Error", "Por favor ingrese el código TOTP")
            return

        try:
            if validate_totp(self.current_user, entered_code):
                messagebox.showinfo("Éxito", "¡Autenticación completa!")
                self.root.destroy()
                self.on_success(self.current_user, self.fernet_key)
            else:
                messagebox.showerror("Error", "Código TOTP incorrecto")
                self.totp_entry.delete(0, tk.END)
                self.totp_entry.focus()
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar TOTP: {str(e)}")
    
    def run(self):
        """Ejecuta la ventana de login"""
        self.root.mainloop()
