# Vista/login.py
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import qrcode
import io
import logging

from controller.login_controller import LoginController

logger = logging.getLogger(__name__)

# Nueva función para mantener compatibilidad con main.py
def start_login(on_success_callback):
    """Función helper para iniciar el login desde main.py"""
    login_window = LoginWindow(on_success_callback)
    login_window.run()

class LoginWindow:
    def __init__(self, on_success_callback):
        self.root = tk.Tk()
        self.root.title("Gestor de Contraseñas - Login")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        self.on_success = on_success_callback
        self.controller = LoginController()
        
        self.setup_styles()
        
        if not self.controller.admin_exists():
            self.show_create_admin_screen()
        else:
            self.show_login_screen()

    def setup_styles(self):
        self.root.configure(bg='#1e1e1e')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', 
                        background='#1e1e1e', 
                        foreground='white',
                        font=('Arial', 16, 'bold'))
        style.configure('Regular.TLabel',
                        background='#1e1e1e',
                        foreground='white',
                        font=('Arial', 10))

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ====================== CREAR ADMIN ======================
    def show_create_admin_screen(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)

        ttk.Label(main_frame, text="Crear Usuario Administrador", 
                    style='Title.TLabel').pack(pady=(0, 30))

        ttk.Label(main_frame, text="Nombre de usuario:", 
                    style='Regular.TLabel').pack(anchor='w', pady=(10, 5))
        self.username_entry = ttk.Entry(main_frame, width=35, font=('Arial', 11))
        self.username_entry.pack(fill='x', pady=5)

        ttk.Label(main_frame, text="Contraseña maestra:", 
                    style='Regular.TLabel').pack(anchor='w', pady=(15, 5))
        self.password_entry = ttk.Entry(main_frame, width=35, show="*", font=('Arial', 11))
        self.password_entry.pack(fill='x', pady=5)

        tk.Button(main_frame, text="Crear Usuario Administrador", 
                    command=self.create_admin,
                    bg='#0d7377', fg='white', font=('Arial', 12, 'bold'),
                    padx=20, pady=12, cursor='hand2', relief='flat').pack(pady=30)

    def create_admin(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        success, message = self.controller.create_admin(username, password)
        
        if success:
            messagebox.showinfo("Éxito", message)
            self.show_totp_qr(username)
        else:
            messagebox.showerror("Error", message)

    # ====================== QR para TOTP ======================
    def show_totp_qr(self, username: str):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)

        ttk.Label(main_frame, text="Configurar Autenticación TOTP", 
                    style='Title.TLabel').pack(pady=(0, 20))

        ttk.Label(main_frame, 
                    text="Escanee este código QR con Google Authenticator, Authy, etc.",
                    style='Regular.TLabel', justify='center').pack(pady=(0, 20))

        uri = self.controller.get_totp_uri(username)
        
        # Validar que el URI fue generado correctamente
        if not uri:
            logger.error("URI TOTP vacío, no se puede generar QR")
            messagebox.showerror("Error", "No se pudo generar el código QR.\nIntente de nuevo.")
            self.show_create_admin_screen()
            return
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=5
            )
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            bio = io.BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            img_tk = ImageTk.PhotoImage(Image.open(bio))

            qr_label = tk.Label(main_frame, image=img_tk, bg='#1e1e1e')
            qr_label.image = img_tk
            qr_label.pack(pady=20)
            
            logger.info(f"QR TOTP mostrado exitosamente para {username}")

        except Exception as e:
            logger.error(f"Error al crear QR: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error al generar código QR: {str(e)}")
            self.show_create_admin_screen()
            return

        ttk.Label(main_frame, 
                    text=f"O ingrese manualmente:\n{self.controller.current_user.totp_secret if self.controller.current_user else ''}",
                    style='Regular.TLabel', justify='center').pack(pady=10)

        tk.Button(main_frame, text="Continuar al Login", 
                    command=self.show_login_screen,
                    bg='#0d7377', fg='white', font=('Arial', 12, 'bold'),
                    padx=20, pady=10, cursor='hand2', relief='flat').pack(pady=20)

    # ====================== PANTALLA DE LOGIN ======================
    def show_login_screen(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)

        title_frame = tk.Frame(main_frame, bg='#1e1e1e')
        title_frame.pack(pady=(0, 30))
        tk.Label(title_frame, text="🔐", font=('Arial', 60), bg='#1e1e1e').pack()
        ttk.Label(title_frame, text="Gestor de Contraseñas", 
                    style='Title.TLabel').pack(pady=5)

        login_frame = tk.Frame(main_frame, bg='#2d2d2d')
        login_frame.pack(fill='both', padx=30, pady=20)
        inner = tk.Frame(login_frame, bg='#2d2d2d')
        inner.pack(padx=30, pady=40)

        ttk.Label(inner, text="Usuario:", background='#2d2d2d', foreground='white', font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=12)
        self.username_entry = ttk.Entry(inner, width=28, font=('Arial', 11))
        self.username_entry.grid(row=0, column=1, padx=15)

        ttk.Label(inner, text="Contraseña:", background='#2d2d2d', foreground='white', font=('Arial', 11)).grid(row=1, column=0, sticky='w', pady=12)
        self.password_entry = ttk.Entry(inner, width=28, show="*", font=('Arial', 11))
        self.password_entry.grid(row=1, column=1, padx=15)

        tk.Button(main_frame, text="Iniciar Sesión", 
                    command=self.attempt_login,
                    bg='#0d7377', fg='white', font=('Arial', 12, 'bold'),
                    padx=40, pady=12, cursor='hand2', relief='flat').pack(pady=25)

        self.root.bind('<Return>', lambda e: self.attempt_login())

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Por favor complete todos los campos")
            return

        success, _, _ = self.controller.authenticate(username, password)

        if success:
            self.show_totp_screen()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    # ====================== VERIFICACIÓN TOTP ======================
    def show_totp_screen(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)

        ttk.Label(main_frame, text="Verificación de Segundo Factor", 
                style='Title.TLabel').pack(pady=(0, 30))

        ttk.Label(main_frame, 
                    text="Ingrese el código de 6 dígitos de su aplicación de autenticación",
                    style='Regular.TLabel').pack(pady=(0, 20))

        self.totp_entry = ttk.Entry(main_frame, width=20, font=('Arial', 20), justify='center')
        self.totp_entry.pack(pady=15)
        self.totp_entry.focus()

        tk.Button(main_frame, text="Verificar Código", 
                    command=self.verify_totp,
                    bg='#0d7377', fg='white', font=('Arial', 12, 'bold'),
                    padx=40, pady=12, cursor='hand2', relief='flat').pack(pady=20)

        self.totp_entry.bind('<Return>', lambda e: self.verify_totp())

    def verify_totp(self):
        code = self.totp_entry.get().strip()
        if not code:
            messagebox.showerror("Error", "Por favor ingrese el código")
            return

        if self.controller.verify_totp_code(code):
            messagebox.showinfo("¡Bienvenido!", "Autenticación completada exitosamente")
            self.root.destroy()
            if self.on_success:
                self.on_success(self.controller.current_user, self.controller.fernet_key)
        else:
            messagebox.showerror("Error", "Código TOTP incorrecto o expirado")
            self.totp_entry.delete(0, tk.END)
            self.totp_entry.focus()

    def run(self):
        """Método para iniciar la ventana"""
        self.root.mainloop()


