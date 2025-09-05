import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
import os
import shutil
import logging
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import subprocess
import platform
import webbrowser
from datetime import datetime
import psutil
import qrcode
from PIL import Image, ImageTk
import io

# Définir UPNP_AVAILABLE
try:
    import miniupnpc
    UPNP_AVAILABLE = True
except ImportError:
    UPNP_AVAILABLE = False

# Import des modules personnalisés
from network_scanner import NetworkScanner
from config_manager import ConfigManager
from upnp_manager import UPnPManager
from web_server import WebServer
from file_manager import FileManager
from qr_code_generator import QRCodeGenerator
from ip_manager import IPManager

class PortForwardingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Port Forwarding Manager Pro")

        # Définir l'icône de la fenêtre
        try:
            self.root.iconbitmap(default='ico.ico')
        except:
            pass

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # Configuration du logging
        if not os.path.exists('logs'):
            os.makedirs('logs')

        logging.basicConfig(
            filename=os.path.join('logs', 'app.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Initialisation des gestionnaires
        self.upnp_manager = UPnPManager()
        self.file_manager = FileManager()
        self.web_server = WebServer(self.file_manager.upload_dir)
        self.network_scanner = NetworkScanner()
        self.ip_manager = IPManager()

        # Variables d'état
        self.server_running = False
        self.port_forwarding_active = False

        # Configuration de l'interface
        self.setup_gui()
        self.load_settings()
        self.refresh_timer = None
        self.start_refresh_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_gui(self):
        """Configurer l'interface utilisateur."""
        self.root.geometry(self.config.get('window_geometry', '1000x700+100+100'))
        self.root.minsize(800, 600)

        # Application du thème
        self.apply_theme(self.config.get('theme', 'light'))

        # Création des onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Création des onglets
        self.create_server_tab()
        self.create_files_tab()
        self.create_network_tab()
        self.create_ip_manager_tab()
        self.create_logs_tab()
        self.create_settings_tab()
        self.create_status_bar()

        # Menu principal
        self.create_menu()

    def apply_theme(self, theme):
        """Appliquer le thème sélectionné."""
        style = ttk.Style()
        if theme == "dark":
            self.root.config(bg="#2d2d2d")
            style.configure("TFrame", background="#2d2d2d")
            style.configure("TLabel", background="#2d2d2d", foreground="white")
            style.configure("TButton", background="#3c3c3c", foreground="white")
            style.configure("TNotebook", background="#2d2d2d")
            style.configure("TNotebook.Tab", background="#3c3c3c", foreground="white")
        else:
            self.root.config(bg="white")
            style.configure("TFrame", background="white")
            style.configure("TLabel", background="white", foreground="black")
            style.configure("TButton", background="#f0f0f0", foreground="black")
            style.configure("TNotebook", background="white")
            style.configure("TNotebook.Tab", background="#f0f0f0", foreground="black")

    def create_menu(self):
        """Créer le menu de l'application."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Upload Files...", command=self.upload_files)
        file_menu.add_command(label="Upload Folder...", command=self.upload_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Open Upload Directory", command=self.open_upload_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Menu Serveur
        server_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Server", menu=server_menu)
        server_menu.add_command(label="Start Server", command=self.toggle_server)
        server_menu.add_command(label="Stop Server", command=self.toggle_server)
        server_menu.add_separator()
        server_menu.add_command(label="Open in Browser", command=self.open_in_browser)

        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Port Scanner", command=self.open_port_scanner)
        tools_menu.add_command(label="Network Info", command=self.show_network_info)
        tools_menu.add_separator()
        tools_menu.add_command(label="Generate QR Code", command=self.generate_qr_code)

        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_server_tab(self):
        """Créer l'onglet de contrôle du serveur."""
        server_frame = ttk.Frame(self.notebook)
        self.notebook.add(server_frame, text="Server Control")

        # État du serveur
        status_frame = ttk.LabelFrame(server_frame, text="Server Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)

        self.server_status_var = tk.StringVar(value="Stopped")
        self.port_status_var = tk.StringVar(value="Not Active")

        ttk.Label(status_frame, text="Server Status:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.server_status_label = ttk.Label(status_frame, textvariable=self.server_status_var, foreground='red')
        self.server_status_label.grid(row=0, column=1, sticky='w')

        ttk.Label(status_frame, text="Port Forwarding:").grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.port_status_label = ttk.Label(status_frame, textvariable=self.port_status_var, foreground='red')
        self.port_status_label.grid(row=1, column=1, sticky='w')

        # Contrôle du serveur
        control_frame = ttk.LabelFrame(server_frame, text="Server Control", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)

        port_frame = ttk.Frame(control_frame)
        port_frame.pack(fill='x', pady=5)

        ttk.Label(port_frame, text="Port:").pack(side='left')
        self.port_var = tk.StringVar(value=str(self.config['port']))
        port_spinbox = ttk.Spinbox(port_frame, from_=1024, to=65535, textvariable=self.port_var, width=10)
        port_spinbox.pack(side='left', padx=5)
        ttk.Button(port_frame, text="Check Port", command=self.check_port).pack(side='left', padx=5)

        self.upnp_var = tk.BooleanVar(value=self.config['upnp_enabled'])
        upnp_check = ttk.Checkbutton(control_frame, text="Enable UPnP Port Forwarding", variable=self.upnp_var)
        upnp_check.pack(anchor='w', pady=5)

        if not UPNP_AVAILABLE:
            upnp_check.config(state='disabled')
            ttk.Label(control_frame, text="UPnP not available (install miniupnpc)", foreground='red').pack(anchor='w')

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', pady=10)

        self.toggle_button = ttk.Button(button_frame, text="Start Server", command=self.toggle_server)
        self.toggle_button.pack(side='left', padx=5)
        ttk.Button(button_frame, text="Open in Browser", command=self.open_in_browser).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Copy URL", command=self.copy_url).pack(side='left', padx=5)

        # Informations de connexion
        info_frame = ttk.LabelFrame(server_frame, text="Connection Information", padding=10)
        info_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.local_url_var = tk.StringVar()
        self.public_url_var = tk.StringVar()

        ttk.Label(info_frame, text="Local URL:").grid(row=0, column=0, sticky='nw', padx=(0, 10))
        ttk.Label(info_frame, textvariable=self.local_url_var, foreground='blue').grid(row=0, column=1, sticky='w')

        ttk.Label(info_frame, text="Public URL:").grid(row=1, column=0, sticky='nw', padx=(0, 10))
        ttk.Label(info_frame, textvariable=self.public_url_var, foreground='blue').grid(row=1, column=1, sticky='w')

        self.qr_frame = ttk.Frame(info_frame)
        self.qr_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.qr_label = ttk.Label(self.qr_frame)
        self.qr_label.pack()

        self.update_connection_info()

    def create_files_tab(self):
        """Créer l'onglet de gestion des fichiers."""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="File Management")

        # Upload de fichiers
        upload_frame = ttk.LabelFrame(files_frame, text="Upload Files", padding=10)
        upload_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(upload_frame, text="Select Files...", command=self.upload_files).pack(side='left', padx=5)
        ttk.Button(upload_frame, text="Upload Folder...", command=self.upload_folder).pack(side='left', padx=5)

        # Liste des fichiers
        list_frame = ttk.LabelFrame(files_frame, text="Uploaded Files", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('Name', 'Size', 'Modified', 'Type')
        self.files_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')

        self.files_tree.heading('#0', text='')
        self.files_tree.column('#0', width=20)

        for col in columns:
            self.files_tree.heading(col, text=col)
            self.files_tree.column(col, width=150)

        v_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.files_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.files_tree.xview)

        self.files_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.files_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        # Menu contextuel
        self.files_context_menu = tk.Menu(self.root, tearoff=0)
        self.files_context_menu.add_command(label="Open", command=self.open_selected_file)
        self.files_context_menu.add_command(label="Rename", command=self.rename_selected_file)
        self.files_context_menu.add_command(label="Delete", command=self.delete_selected_file)
        self.files_context_menu.add_separator()
        self.files_context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)

        self.files_tree.bind("<Button-3>", self.show_files_context_menu)
        self.files_tree.bind("<Double-1>", self.open_selected_file)

        # Boutons d'action
        ops_frame = ttk.Frame(list_frame)
        ops_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')

        ttk.Button(ops_frame, text="Refresh", command=self.refresh_files_list).pack(side='left', padx=5)
        ttk.Button(ops_frame, text="Delete Selected", command=self.delete_selected_file).pack(side='left', padx=5)
        ttk.Button(ops_frame, text="Open Folder", command=self.open_upload_directory).pack(side='left', padx=5)

        self.refresh_files_list()

    def create_network_tab(self):
        """Créer l'onglet des informations réseau."""
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="Network Info")

        # Informations réseau
        info_frame = ttk.LabelFrame(network_frame, text="Network Information", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)

        self.network_info_text = scrolledtext.ScrolledText(info_frame, height=10, wrap=tk.WORD)
        self.network_info_text.pack(fill='both', expand=True)

        ttk.Button(info_frame, text="Refresh Network Info", command=self.refresh_network_info).pack(pady=5)

        # Mappage UPnP
        upnp_frame = ttk.LabelFrame(network_frame, text="UPnP Port Mappings", padding=10)
        upnp_frame.pack(fill='both', expand=True, padx=10, pady=5)

        upnp_columns = ('External Port', 'Protocol', 'Internal IP', 'Internal Port', 'Description')
        self.upnp_tree = ttk.Treeview(upnp_frame, columns=upnp_columns, show='headings')

        for col in upnp_columns:
            self.upnp_tree.heading(col, text=col)
            self.upnp_tree.column(col, width=120)

        upnp_v_scroll = ttk.Scrollbar(upnp_frame, orient='vertical', command=self.upnp_tree.yview)
        self.upnp_tree.configure(yscrollcommand=upnp_v_scroll.set)

        self.upnp_tree.pack(side='left', fill='both', expand=True)
        upnp_v_scroll.pack(side='right', fill='y')

        ttk.Button(upnp_frame, text="Refresh UPnP Mappings", command=self.refresh_upnp_mappings).pack(pady=5)

        self.refresh_network_info()
        self.refresh_upnp_mappings()

    def create_ip_manager_tab(self):
        """Créer l'onglet de gestion des adresses IP."""
        ip_frame = ttk.Frame(self.notebook)
        self.notebook.add(ip_frame, text="IP Management")

        # Liste des adresses IP autorisées
        allowed_ip_frame = ttk.LabelFrame(ip_frame, text="Allowed IPs", padding=10)
        allowed_ip_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('IP Address', 'Status')
        self.allowed_ip_tree = ttk.Treeview(allowed_ip_frame, columns=columns, show='headings')

        for col in columns:
            self.allowed_ip_tree.heading(col, text=col)
            self.allowed_ip_tree.column(col, width=150)

        v_scrollbar = ttk.Scrollbar(allowed_ip_frame, orient='vertical', command=self.allowed_ip_tree.yview)
        self.allowed_ip_tree.configure(yscrollcommand=v_scrollbar.set)

        self.allowed_ip_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')

        # Menu contextuel pour les adresses IP
        self.ip_context_menu = tk.Menu(self.root, tearoff=0)
        self.ip_context_menu.add_command(label="Remove", command=self.remove_selected_ip)

        self.allowed_ip_tree.bind("<Button-3>", self.show_ip_context_menu)

        # Ajouter une adresse IP
        add_ip_frame = ttk.Frame(allowed_ip_frame)
        add_ip_frame.pack(fill='x', pady=5)

        ttk.Label(add_ip_frame, text="IP Address:").pack(side='left')
        self.new_ip_var = tk.StringVar()
        ttk.Entry(add_ip_frame, textvariable=self.new_ip_var, width=20).pack(side='left', padx=5)
        ttk.Button(add_ip_frame, text="Add IP", command=self.add_ip).pack(side='left', padx=5)

        # Liste des adresses IP bloquées
        blocked_ip_frame = ttk.LabelFrame(ip_frame, text="Blocked IPs", padding=10)
        blocked_ip_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.blocked_ip_tree = ttk.Treeview(blocked_ip_frame, columns=columns, show='headings')

        for col in columns:
            self.blocked_ip_tree.heading(col, text=col)
            self.blocked_ip_tree.column(col, width=150)

        v_scrollbar_blocked = ttk.Scrollbar(blocked_ip_frame, orient='vertical', command=self.blocked_ip_tree.yview)
        self.blocked_ip_tree.configure(yscrollcommand=v_scrollbar_blocked.set)

        self.blocked_ip_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar_blocked.pack(side='right', fill='y')

        # Menu contextuel pour les adresses IP bloquées
        self.blocked_ip_context_menu = tk.Menu(self.root, tearoff=0)
        self.blocked_ip_context_menu.add_command(label="Unblock", command=self.unblock_selected_ip)

        self.blocked_ip_tree.bind("<Button-3>", self.show_blocked_ip_context_menu)

        # Ajouter une adresse IP bloquée
        add_blocked_ip_frame = ttk.Frame(blocked_ip_frame)
        add_blocked_ip_frame.pack(fill='x', pady=5)

        ttk.Label(add_blocked_ip_frame, text="IP Address:").pack(side='left')
        self.new_blocked_ip_var = tk.StringVar()
        ttk.Entry(add_blocked_ip_frame, textvariable=self.new_blocked_ip_var, width=20).pack(side='left', padx=5)
        ttk.Button(add_blocked_ip_frame, text="Block IP", command=self.block_ip).pack(side='left', padx=5)

        # Rafraîchir les listes
        self.refresh_ip_lists()

    def create_logs_tab(self):
        """Créer l'onglet des logs."""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")

        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD)
        self.logs_text.pack(fill='both', expand=True, padx=10, pady=5)

        logs_control = ttk.Frame(logs_frame)
        logs_control.pack(fill='x', padx=10, pady=5)

        ttk.Button(logs_control, text="Refresh Logs", command=self.refresh_logs).pack(side='left', padx=5)
        ttk.Button(logs_control, text="Clear Logs", command=self.clear_logs).pack(side='left', padx=5)
        ttk.Button(logs_control, text="Save Logs", command=self.save_logs).pack(side='left', padx=5)

        self.auto_refresh_logs_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(logs_control, text="Auto-refresh", variable=self.auto_refresh_logs_var).pack(side='right')

        self.refresh_logs()

    def create_settings_tab(self):
        """Créer l'onglet des paramètres."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Paramètres généraux
        general_frame = ttk.LabelFrame(scrollable_frame, text="General Settings", padding=10)
        general_frame.pack(fill='x', padx=10, pady=5)

        port_frame = ttk.Frame(general_frame)
        port_frame.pack(fill='x', pady=2)

        ttk.Label(port_frame, text="Default Port:").pack(side='left')
        self.default_port_var = tk.StringVar(value=str(self.config['port']))
        ttk.Spinbox(port_frame, from_=1024, to=65535, textvariable=self.default_port_var, width=10).pack(side='left', padx=5)

        self.auto_start_var = tk.BooleanVar(value=self.config['auto_start'])
        ttk.Checkbutton(general_frame, text="Auto-start server on launch", variable=self.auto_start_var).pack(anchor='w', pady=2)

        # Paramètres de téléchargement
        upload_frame = ttk.LabelFrame(scrollable_frame, text="File Upload Settings", padding=10)
        upload_frame.pack(fill='x', padx=10, pady=5)

        size_frame = ttk.Frame(upload_frame)
        size_frame.pack(fill='x', pady=2)

        ttk.Label(size_frame, text="Max File Size (MB):").pack(side='left')
        self.max_size_var = tk.StringVar(value=str(self.config['max_file_size']))
        ttk.Spinbox(size_frame, from_=1, to=1000, textvariable=self.max_size_var, width=10).pack(side='left', padx=5)

        ttk.Label(upload_frame, text="Allowed Extensions:").pack(anchor='w', pady=(5, 0))
        self.extensions_text = tk.Text(upload_frame, height=3, wrap=tk.WORD)
        self.extensions_text.pack(fill='x', pady=2)
        self.extensions_text.insert('1.0', ', '.join(self.config['allowed_extensions']))

        # Paramètres de sécurité
        security_frame = ttk.LabelFrame(scrollable_frame, text="Security Settings", padding=10)
        security_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(security_frame, text="⚠️ Always be cautious when port forwarding", foreground='orange').pack(anchor='w')
        ttk.Label(security_frame, text="Only forward ports when necessary", foreground='gray').pack(anchor='w')

        # Paramètres d'apparence
        appearance_frame = ttk.LabelFrame(scrollable_frame, text="Appearance", padding=10)
        appearance_frame.pack(fill='x', padx=10, pady=5)

        theme_frame = ttk.Frame(appearance_frame)
        theme_frame.pack(fill='x', pady=2)

        ttk.Label(theme_frame, text="Theme:").pack(side='left')
        self.theme_var = tk.StringVar(value=self.config['theme'])
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=['light', 'dark'], width=10)
        theme_combo.pack(side='left', padx=5)

        # Boutons de sauvegarde
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(buttons_frame, text="Save Settings", command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Reset to Defaults", command=self.reset_settings).pack(side='left', padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_status_bar(self):
        """Créer la barre de statut."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x')

        self.status_text = tk.StringVar(value="Ready")
        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side='left', padx=5)

        ttk.Separator(self.status_bar, orient='vertical').pack(side='right', fill='y', padx=5)

        self.system_info = tk.StringVar()
        ttk.Label(self.status_bar, textvariable=self.system_info).pack(side='right', padx=5)

        self.update_system_info()

    def load_settings(self):
        """Charger les paramètres depuis la configuration."""
        self.port_var.set(str(self.config['port']))
        self.upnp_var.set(self.config['upnp_enabled'])

    def save_settings(self):
        """Sauvegarder les paramètres actuels dans la configuration."""
        try:
            self.config['port'] = int(self.default_port_var.get())
            self.config['auto_start'] = self.auto_start_var.get()
            self.config['max_file_size'] = int(self.max_size_var.get())
            self.config['theme'] = self.theme_var.get()
            self.config['window_geometry'] = self.root.geometry()

            extensions_text = self.extensions_text.get('1.0', tk.END).strip()
            extensions = [ext.strip() for ext in extensions_text.split(',') if ext.strip()]
            self.config['allowed_extensions'] = extensions

            self.config_manager.save_config(self.config)
            messagebox.showinfo("Settings", "Settings saved successfully!")
            self.status_text.set("Settings saved")

            # Appliquer le thème immédiatement
            self.apply_theme(self.config['theme'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            logging.error(f"Failed to save settings: {e}")

    def reset_settings(self):
        """Réinitialiser les paramètres aux valeurs par défaut."""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            self.config = self.config_manager.default_config.copy()
            self.config_manager.save_config(self.config)
            messagebox.showinfo("Settings", "Settings reset to defaults!")
            self.load_settings()

    def toggle_server(self):
        """Basculer le serveur web."""
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        """Démarrer le serveur web."""
        try:
            port = int(self.port_var.get())
            if not self.network_scanner.is_port_available(port):
                messagebox.showerror("Error", f"Port {port} is already in use!")
                return

            # Vérifiez que le dossier uploaded_files existe
            if not os.path.exists(self.file_manager.upload_dir):
                os.makedirs(self.file_manager.upload_dir)

            if self.web_server.start_server(port, self.ip_manager):
                self.server_running = True
                self.server_status_var.set("Running")
                self.server_status_label.config(foreground='green')
                self.toggle_button.config(text="Stop Server")

                if self.upnp_var.get() and UPNP_AVAILABLE:
                    if self.upnp_manager.add_port_mapping(port):
                        self.port_forwarding_active = True
                        self.port_status_var.set("Active")
                        self.port_status_label.config(foreground='green')
                        self.status_text.set(f"Server started with port forwarding on port {port}")
                    else:
                        messagebox.showwarning("UPnP Warning", "Server started but UPnP port forwarding failed")
                        self.status_text.set(f"Server started on port {port} (UPnP failed)")
                else:
                    self.status_text.set(f"Server started on port {port}")

                self.update_connection_info()
                logging.info(f"Server started successfully on port {port}")
            else:
                messagebox.showerror("Error", "Failed to start server!")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            logging.error(f"Failed to start server: {e}")

    def stop_server(self):
        """Arrêter le serveur web."""
        try:
            self.web_server.stop_server()
            self.server_running = False
            self.server_status_var.set("Stopped")
            self.server_status_label.config(foreground='red')
            self.toggle_button.config(text="Start Server")

            if self.port_forwarding_active:
                port = int(self.port_var.get())
                self.upnp_manager.delete_port_mapping(port)
                self.port_forwarding_active = False
                self.port_status_var.set("Not Active")
                self.port_status_label.config(foreground='red')

            self.status_text.set("Server stopped")
            self.update_connection_info()
            logging.info("Server stopped successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
            logging.error(f"Failed to stop server: {e}")

    def check_port(self):
        """Vérifier si le port sélectionné est disponible."""
        try:
            port = int(self.port_var.get())
            if self.network_scanner.is_port_available(port):
                messagebox.showinfo("Port Check", f"Port {port} is available!")
            else:
                messagebox.showwarning("Port Check", f"Port {port} is already in use!")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number!")

    def upload_files(self):
        """Télécharger plusieurs fichiers."""
        file_paths = filedialog.askopenfilenames(
            title="Select files to upload",
            initialdir=self.config['last_directory'],
            filetypes=[
                ("Web files", "*.html *.css *.js *.png *.jpg *.jpeg *.gif *.ico"),
                ("All files", "*.*")
            ]
        )

        if file_paths:
            self.config['last_directory'] = os.path.dirname(file_paths[0])
            uploaded_count = 0
            failed_count = 0

            for file_path in file_paths:
                try:
                    self.file_manager.upload_file(
                        file_path,
                        self.config['max_file_size'],
                        self.config['allowed_extensions']
                    )
                    uploaded_count += 1
                except Exception as e:
                    failed_count += 1
                    logging.error(f"Failed to upload {file_path}: {e}")

            message = f"Uploaded {uploaded_count} files successfully"
            if failed_count > 0:
                message += f", {failed_count} files failed"

            messagebox.showinfo("Upload Complete", message)
            self.refresh_files_list()
            self.status_text.set(message)

    def upload_folder(self):
        """Télécharger tous les fichiers d'un dossier."""
        folder_path = filedialog.askdirectory(
            title="Select folder to upload",
            initialdir=self.config['last_directory']
        )

        if folder_path:
            self.config['last_directory'] = folder_path
            uploaded_count = 0
            failed_count = 0

            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        self.file_manager.upload_file(
                            file_path,
                            self.config['max_file_size'],
                            self.config['allowed_extensions']
                        )
                        uploaded_count += 1
                    except Exception as e:
                        failed_count += 1
                        logging.error(f"Failed to upload {file_path}: {e}")

            message = f"Uploaded {uploaded_count} files from folder"
            if failed_count > 0:
                message += f", {failed_count} files failed"

            messagebox.showinfo("Upload Complete", message)
            self.refresh_files_list()
            self.status_text.set(message)

    def refresh_files_list(self):
        """Rafraîchir la liste des fichiers."""
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        files_info = self.file_manager.list_files()

        for file_info in files_info:
            size_mb = file_info['size'] / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_info['size']} bytes"
            file_type = os.path.splitext(file_info['name'])[1].upper()

            self.files_tree.insert('', 'end', values=(
                file_info['name'],
                size_str,
                file_info['modified'].strftime("%Y-%m-%d %H:%M:%S"),
                file_type
            ))

    def show_files_context_menu(self, event):
        """Afficher le menu contextuel pour les fichiers."""
        selection = self.files_tree.selection()
        if selection:
            self.files_context_menu.post(event.x_root, event.y_root)

    def open_selected_file(self, event=None):
        """Ouvrir le fichier sélectionné dans le programme par défaut."""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            file_name = item['values'][0]
            file_path = os.path.join(self.file_manager.upload_dir, file_name)

            try:
                if platform.system() == 'Darwin':
                    subprocess.call(('open', file_path))
                elif platform.system() == 'Windows':
                    os.startfile(file_path)
                else:
                    subprocess.call(('xdg-open', file_path))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def rename_selected_file(self):
        """Renommer le fichier sélectionné."""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            old_name = item['values'][0]
            new_name = tk.simpledialog.askstring("Rename File", f"New name for '{old_name}':", initialvalue=old_name)

            if new_name and new_name != old_name:
                if self.file_manager.rename_file(old_name, new_name):
                    messagebox.showinfo("Success", "File renamed successfully!")
                    self.refresh_files_list()
                else:
                    messagebox.showerror("Error", "Failed to rename file!")

    def delete_selected_file(self):
        """Supprimer le fichier sélectionné."""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            file_name = item['values'][0]

            if messagebox.askyesno("Delete File", f"Delete '{file_name}'?"):
                if self.file_manager.delete_file(file_name):
                    messagebox.showinfo("Success", "File deleted successfully!")
                    self.refresh_files_list()
                else:
                    messagebox.showerror("Error", "Failed to delete file!")

    def show_in_explorer(self):
        """Afficher le fichier sélectionné dans l'explorateur de fichiers."""
        selection = self.files_tree.selection()
        if selection:
            item = self.files_tree.item(selection[0])
            file_name = item['values'][0]
            file_path = os.path.join(self.file_manager.upload_dir, file_name)

            try:
                if platform.system() == 'Windows':
                    subprocess.run(['explorer', '/select,', file_path])
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', '-R', file_path])
                else:
                    subprocess.run(['xdg-open', os.path.dirname(file_path)])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open explorer: {e}")

    def open_upload_directory(self):
        """Ouvrir le répertoire de téléchargement dans l'explorateur de fichiers."""
        try:
            if platform.system() == 'Windows':
                os.startfile(self.file_manager.upload_dir)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', self.file_manager.upload_dir])
            else:
                subprocess.call(['xdg-open', self.file_manager.upload_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {e}")

    def update_connection_info(self):
        """Mettre à jour les informations de connexion."""
        port = int(self.port_var.get()) if self.port_var.get().isdigit() else 8080
        local_ip = self.network_scanner.get_local_ip()
        self.local_url_var.set(f"http://{local_ip}:{port}")

        if self.upnp_var.get() and UPNP_AVAILABLE:
            public_ip = self.upnp_manager.get_public_ip()
            if public_ip:
                self.public_url_var.set(f"http://{public_ip}:{port}")
            else:
                self.public_url_var.set("UPnP not available")
        else:
            self.public_url_var.set("UPnP disabled")

    def open_in_browser(self):
        """Ouvrir l'URL locale dans le navigateur."""
        try:
            url = self.local_url_var.get()
            if url:
                webbrowser.open(url)
            else:
                messagebox.showwarning("Warning", "No URL available!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {e}")

    def copy_url(self):
        """Copier l'URL dans le presse-papiers."""
        try:
            url = self.local_url_var.get()
            if self.port_forwarding_active:
                url = self.public_url_var.get()

            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.status_text.set("URL copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy URL: {e}")

    def generate_qr_code(self):
        """Générer un code QR pour l'URL actuelle."""
        try:
            url = self.local_url_var.get()
            if self.port_forwarding_active and self.public_url_var.get() != "UPnP disabled":
                url = self.public_url_var.get()

            if url and url not in ["UPnP disabled", "UPnP not available"]:
                qr_image = QRCodeGenerator.generate_qr_code(url, 150)
                self.qr_label.config(image=qr_image)
                self.qr_label.image = qr_image
                self.status_text.set("QR code generated")
            else:
                messagebox.showwarning("Warning", "No valid URL available for QR code!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate QR code: {e}")

    def refresh_network_info(self):
        """Rafraîchir les informations réseau."""
        try:
            info_lines = []
            info_lines.append("=== Network Information ===\n")

            local_ip = self.network_scanner.get_local_ip()
            info_lines.append(f"Local IP Address: {local_ip}")

            if UPNP_AVAILABLE:
                public_ip = self.upnp_manager.get_public_ip()
                info_lines.append(f"Public IP Address: {public_ip or 'Not available'}")
            else:
                info_lines.append("Public IP Address: UPnP not available")

            info_lines.append("\n=== Network Interfaces ===")
            for interface, addrs in psutil.net_if_addrs().items():
                info_lines.append(f"\n{interface}:")
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        info_lines.append(f"  IPv4: {addr.address}")
                    elif addr.family == socket.AF_INET6:
                        info_lines.append(f"  IPv6: {addr.address}")

            info_lines.append("\n=== Network Statistics ===")
            net_stats = psutil.net_io_counters()
            info_lines.append(f"Bytes Sent: {net_stats.bytes_sent:,}")
            info_lines.append(f"Bytes Received: {net_stats.bytes_recv:,}")
            info_lines.append(f"Packets Sent: {net_stats.packets_sent:,}")
            info_lines.append(f"Packets Received: {net_stats.packets_recv:,}")

            self.network_info_text.delete('1.0', tk.END)
            self.network_info_text.insert('1.0', '\n'.join(info_lines))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh network info: {e}")

    def refresh_upnp_mappings(self):
        """Rafraîchir la liste des règles de transfert de port UPnP."""
        for item in self.upnp_tree.get_children():
            self.upnp_tree.delete(item)

        if UPNP_AVAILABLE:
            try:
                mappings = self.upnp_manager.list_port_mappings()
                for mapping in mappings:
                    self.upnp_tree.insert('', 'end', values=(
                        mapping['external_port'],
                        mapping['protocol'],
                        mapping['internal_ip'],
                        mapping['internal_port'],
                        mapping['description']
                    ))
            except Exception as e:
                logging.error(f"Failed to refresh UPnP mappings: {e}")

    def open_port_scanner(self):
        """Ouvrir la fenêtre de scanner de ports."""
        scanner_window = tk.Toplevel(self.root)
        scanner_window.title("Port Scanner")
        scanner_window.geometry("500x400")
        scanner_window.resizable(True, True)

        # Définir l'icône de la fenêtre
        try:
            scanner_window.iconbitmap(default='ico.ico')
        except:
            pass

        input_frame = ttk.LabelFrame(scanner_window, text="Scan Parameters", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(input_frame, text="Host:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        host_var = tk.StringVar(value=self.network_scanner.get_local_ip())
        ttk.Entry(input_frame, textvariable=host_var, width=20).grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Port Range:").grid(row=1, column=0, sticky='w', padx=(0, 5))
        start_port_var = tk.StringVar(value="1024")
        end_port_var = tk.StringVar(value="1100")

        port_frame = ttk.Frame(input_frame)
        port_frame.grid(row=1, column=1, padx=5)

        ttk.Entry(port_frame, textvariable=start_port_var, width=8).pack(side='left')
        ttk.Label(port_frame, text=" - ").pack(side='left')
        ttk.Entry(port_frame, textvariable=end_port_var, width=8).pack(side='left')

        results_frame = ttk.LabelFrame(scanner_window, text="Scan Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)

        results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD)
        results_text.pack(fill='both', expand=True)

        def scan_ports():
            try:
                host = host_var.get()
                start_port = int(start_port_var.get())
                end_port = int(end_port_var.get())

                results_text.delete('1.0', tk.END)
                results_text.insert(tk.END, f"Scanning {host} from port {start_port} to {end_port}...\n\n")
                scanner_window.update()

                open_ports = self.network_scanner.scan_ports(host, start_port, end_port)

                if open_ports:
                    results_text.insert(tk.END, f"Found {len(open_ports)} open ports:\n")
                    for port in open_ports:
                        results_text.insert(tk.END, f"Port {port} is open\n")
                else:
                    results_text.insert(tk.END, "No open ports found in the specified range.\n")
            except ValueError:
                messagebox.showerror("Error", "Invalid port numbers!")
            except Exception as e:
                messagebox.showerror("Error", f"Scan failed: {e}")

        ttk.Button(input_frame, text="Start Scan", command=scan_ports).grid(row=2, column=1, pady=10)

    def show_network_info(self):
        """Afficher les informations réseau détaillées."""
        info_window = tk.Toplevel(self.root)
        info_window.title("Network Information")
        info_window.geometry("600x500")

        # Définir l'icône de la fenêtre
        try:
            info_window.iconbitmap(default='ico.ico')
        except:
            pass

        text_area = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
        text_area.pack(fill='both', expand=True, padx=10, pady=10)

        try:
            info_lines = []
            info_lines.append("=== Detailed Network Information ===\n")
            info_lines.append(f"System: {platform.system()} {platform.release()}")
            info_lines.append(f"Machine: {platform.machine()}")
            info_lines.append(f"Processor: {platform.processor()}")

            memory = psutil.virtual_memory()
            info_lines.append(f"\nMemory Total: {memory.total / (1024**3):.2f} GB")
            info_lines.append(f"Memory Available: {memory.available / (1024**3):.2f} GB")
            info_lines.append(f"Memory Used: {memory.percent}%")

            disk = psutil.disk_usage('/')
            info_lines.append(f"\nDisk Total: {disk.total / (1024**3):.2f} GB")
            info_lines.append(f"Disk Free: {disk.free / (1024**3):.2f} GB")
            info_lines.append(f"Disk Used: {(disk.used / disk.total) * 100:.1f}%")

            info_lines.append(f"\n=== Network Interfaces Details ===")
            for interface, addrs in psutil.net_if_addrs().items():
                info_lines.append(f"\n{interface}:")
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        info_lines.append(f"  IPv4: {addr.address}")
                        info_lines.append(f"  Netmask: {addr.netmask}")
                    elif addr.family == socket.AF_INET6:
                        info_lines.append(f"  IPv6: {addr.address}")

            text_area.insert('1.0', '\n'.join(info_lines))
        except Exception as e:
            text_area.insert('1.0', f"Error retrieving network information: {e}")

    def refresh_logs(self):
        """Rafraîchir l'affichage des logs."""
        try:
            log_file = os.path.join('logs', 'app.log')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    if len(lines) > 1000:
                        lines = lines[-1000:]
                        content = '\n'.join(lines)

                    self.logs_text.delete('1.0', tk.END)
                    self.logs_text.insert('1.0', content)
                    self.logs_text.see(tk.END)
            else:
                self.logs_text.delete('1.0', tk.END)
                self.logs_text.insert('1.0', "No logs available yet.")
        except Exception as e:
            self.logs_text.delete('1.0', tk.END)
            self.logs_text.insert('1.0', f"Error reading logs: {e}")

    def clear_logs(self):
        """Effacer les logs."""
        if messagebox.askyesno("Clear Logs", "Clear all logs?"):
            try:
                log_file = os.path.join('logs', 'app.log')
                with open(log_file, 'w') as f:
                    f.write("")

                self.refresh_logs()
                self.status_text.set("Logs cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear logs: {e}")

    def save_logs(self):
        """Sauvegarder les logs dans un fichier."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save logs",
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'w') as f:
                    f.write(self.logs_text.get('1.0', tk.END))

                messagebox.showinfo("Success", "Logs saved successfully!")
                self.status_text.set("Logs saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")

    def update_system_info(self):
        """Mettre à jour les informations système dans la barre de statut."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            self.system_info.set(f"CPU: {cpu_percent}% | RAM: {memory_percent}%")
        except:
            self.system_info.set("System info unavailable")

    def start_refresh_timer(self):
        """Démarrer le timer de rafraîchissement automatique."""
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)

        self.update_system_info()

        if hasattr(self, 'auto_refresh_logs_var') and self.auto_refresh_logs_var.get():
            if self.notebook.index(self.notebook.select()) == 3:
                self.refresh_logs()

        self.refresh_timer = self.root.after(5000, self.start_refresh_timer)

    def show_about(self):
        """Afficher la fenêtre 'À propos'."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Port Forwarding Manager Pro")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()

        # Définir l'icône de la fenêtre
        try:
            about_window.iconbitmap(default='ico.ico')
        except:
            pass

        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill='both', expand=True)

        title_label = ttk.Label(frame, text="Port Forwarding Manager Pro", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        info_text = """Version 1.0.0
A comprehensive port forwarding and file sharing application
with modern GUI and advanced features.

Features:
• Web server with file hosting
• UPnP automatic port forwarding
• File management with drag & drop
• Network scanning and monitoring
• QR code generation for easy sharing
• IP management for security
• Detailed logging and monitoring
• Professional interface

© 2024 Port Forwarding Manager Pro"""

        ttk.Label(frame, text=info_text, justify='center').pack(pady=10)
        ttk.Button(frame, text="Close", command=about_window.destroy).pack(pady=10)

    def on_closing(self):
        """Gérer la fermeture de l'application."""
        self.config['window_geometry'] = self.root.geometry()
        self.config_manager.save_config(self.config)

        if self.server_running:
            self.stop_server()

        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)

        self.root.destroy()

    def add_ip(self):
        """Ajouter une adresse IP autorisée."""
        ip_address = self.new_ip_var.get().strip()
        if ip_address:
            if self.ip_manager.add_allowed_ip(ip_address):
                messagebox.showinfo("Success", f"IP {ip_address} added to allowed list!")
                self.refresh_ip_lists()
                self.new_ip_var.set("")
            else:
                messagebox.showerror("Error", f"Failed to add IP {ip_address}.")

    def remove_selected_ip(self):
        """Supprimer une adresse IP autorisée."""
        selection = self.allowed_ip_tree.selection()
        if selection:
            item = self.allowed_ip_tree.item(selection[0])
            ip_address = item['values'][0]
            if messagebox.askyesno("Remove IP", f"Remove {ip_address} from allowed list?"):
                if self.ip_manager.remove_allowed_ip(ip_address):
                    messagebox.showinfo("Success", f"IP {ip_address} removed from allowed list!")
                    self.refresh_ip_lists()
                else:
                    messagebox.showerror("Error", f"Failed to remove IP {ip_address}.")

    def block_ip(self):
        """Bloquer une adresse IP."""
        ip_address = self.new_blocked_ip_var.get().strip()
        if ip_address:
            if self.ip_manager.add_blocked_ip(ip_address):
                messagebox.showinfo("Success", f"IP {ip_address} added to blocked list!")
                self.refresh_ip_lists()
                self.new_blocked_ip_var.set("")
            else:
                messagebox.showerror("Error", f"Failed to block IP {ip_address}.")

    def unblock_selected_ip(self):
        """Débloquer une adresse IP."""
        selection = self.blocked_ip_tree.selection()
        if selection:
            item = self.blocked_ip_tree.item(selection[0])
            ip_address = item['values'][0]
            if messagebox.askyesno("Unblock IP", f"Unblock {ip_address}?"):
                if self.ip_manager.remove_blocked_ip(ip_address):
                    messagebox.showinfo("Success", f"IP {ip_address} unblocked!")
                    self.refresh_ip_lists()
                else:
                    messagebox.showerror("Error", f"Failed to unblock IP {ip_address}.")

    def show_ip_context_menu(self, event):
        """Afficher le menu contextuel pour les adresses IP autorisées."""
        selection = self.allowed_ip_tree.selection()
        if selection:
            self.ip_context_menu.post(event.x_root, event.y_root)

    def show_blocked_ip_context_menu(self, event):
        """Afficher le menu contextuel pour les adresses IP bloquées."""
        selection = self.blocked_ip_tree.selection()
        if selection:
            self.blocked_ip_context_menu.post(event.x_root, event.y_root)

    def refresh_ip_lists(self):
        """Rafraîchir les listes des adresses IP autorisées et bloquées."""
        for item in self.allowed_ip_tree.get_children():
            self.allowed_ip_tree.delete(item)

        for item in self.blocked_ip_tree.get_children():
            self.blocked_ip_tree.delete(item)

        allowed_ips = self.ip_manager.get_allowed_ips()
        for ip in allowed_ips:
            self.allowed_ip_tree.insert('', 'end', values=(ip, "Allowed"))

        blocked_ips = self.ip_manager.get_blocked_ips()
        for ip in blocked_ips:
            self.blocked_ip_tree.insert('', 'end', values=(ip, "Blocked"))

def main():
    """Point d'entrée principal de l'application."""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

    try:
        root = tk.Tk()
        app = PortForwardingGUI(root)

        if app.config['auto_start']:
            root.after(100, app.start_server)

        root.mainloop()
    except Exception as e:
        logging.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()
