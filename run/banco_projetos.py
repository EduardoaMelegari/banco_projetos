import os
import tkinter as tk
from tkinter import messagebox, ttk
import struct
import tempfile
import shutil
import subprocess
import sys
import json
import re
import threading

# Importações específicas do Windows (só carrega se estiver no Windows)
if sys.platform == "win32":
    try:
        import win32clipboard
        from win32con import CF_HDROP
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

# Importar módulo Firebase Sync
try:
    from firebase_sync import FirebaseSync
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase não disponível. Usando modo local.")

# Importar módulo de autenticação
try:
    from auth import AuthManager
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("⚠️ Módulo de autenticação não disponível.")

# ======= CONFIGURAÇÕES =======
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "app_config.json")

# Configurações padrão
DEFAULT_CONFIG = {
    "pasta_dwgs": os.path.join(os.path.dirname(SCRIPT_DIR), "CONTROLE"),
    "tema": "clam",
    "mostrar_todos_ao_iniciar": True,
    "nome_arquivo_copia": "PROJETO.dwg",
    "usar_firebase": True,  # Usar Firebase Storage por padrão
    "sincronizar_ao_iniciar": True
}

def carregar_config():
    """Carrega configurações do arquivo JSON ou usa padrão"""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config.update(json.load(f))
        except:
            pass
    return config

def salvar_config(config):
    """Salva configurações no arquivo JSON"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except:
        pass

CONFIG = carregar_config()

# Determina o caminho da pasta CONTROLE
PASTA_DWGS = CONFIG["pasta_dwgs"]
if not os.path.exists(PASTA_DWGS):
    PASTA_DWGS = CONFIG["pasta_dwgs_windows"]

# =============================

class BuscaDWG:
    def __init__(self, root, username=None):
        self.root = root
        self.username = username
        titulo = "Banco de Projetos"
        if username:
            titulo += f" [👤 {username}]"
        self.root.title(titulo)
        self.root.geometry("850x550")
        self.root.minsize(650, 450)
        
        # Configurar tema
        self.style = ttk.Style()
        try:
            self.style.theme_use(CONFIG.get("tema", "clam"))
        except:
            pass
        
        # Variáveis
        self.arquivos_cache = []
        self.ordem_atual = {"coluna": None, "reverso": False}
        self.firebase_sync = None
        self.usando_firebase = False
        
        # Configurar interface primeiro (para criar label_status)
        self.criar_interface()
        self.configurar_atalhos()
        
        # Inicializar Firebase se configurado (após interface criada)
        if CONFIG.get("usar_firebase", True) and FIREBASE_AVAILABLE:
            self.inicializar_firebase()
        
        # Carregar arquivos
        self.carregar_arquivos()
        
        # Mostrar todos ao iniciar se configurado
        if CONFIG.get("mostrar_todos_ao_iniciar", True):
            self.buscar_arquivos()
        
        # Focar no campo de busca
        self.entrada.focus_set()
    
    def inicializar_firebase(self):
        """Inicializa conexão com Firebase"""
        try:
            self.firebase_sync = FirebaseSync()
            self.usando_firebase = True
            
            # Sincronizar ao iniciar se configurado
            if CONFIG.get("sincronizar_ao_iniciar", True):
                self.mostrar_status("🔄 Sincronizando com Firebase...", "blue")
                
                # Fazer sync em thread separada para não travar a UI
                def sync_thread():
                    try:
                        self.firebase_sync.download_all()
                        self.root.after(0, lambda: self.mostrar_status("✓ Sincronizado com Firebase", "green"))
                        # Recarregar lista após sincronização (sem baixar novamente)
                        self.root.after(0, self.carregar_arquivos)
                        self.root.after(0, self.buscar_arquivos)
                    except Exception as e:
                        self.root.after(0, lambda: self.mostrar_status(f"⚠ Erro sync: {str(e)[:30]}", "orange"))
                
                threading.Thread(target=sync_thread, daemon=True).start()
            
        except Exception as e:
            self.mostrar_status(f"⚠ Firebase offline: {str(e)[:40]}", "orange")
            self.usando_firebase = False
            print(f"Firebase não inicializado: {e}")
    
    def criar_interface(self):
        """Cria toda a interface gráfica"""
        # Frame principal com padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === FRAME DE BUSCA ===
        frame_busca = ttk.LabelFrame(main_frame, text="Busca", padding="5")
        frame_busca.pack(fill=tk.X, pady=(0, 5))
        
        # Campo de busca
        ttk.Label(frame_busca, text="🔍 Pesquisar:").pack(side=tk.LEFT, padx=3)
        self.entrada = ttk.Entry(frame_busca, width=30, font=("Arial", 10))
        self.entrada.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        # Filtro por tipo
        ttk.Label(frame_busca, text="Tipo:").pack(side=tk.LEFT, padx=(10, 3))
        self.combo_filtro = ttk.Combobox(
            frame_busca,
            values=["Todos", "Bifásico", "Trifásico", "Trafo", "Rural", "Indefinido"],
            state="readonly", 
            width=12
        )
        self.combo_filtro.set("Todos")
        self.combo_filtro.pack(side=tk.LEFT, padx=3)
        
        # Botão limpar
        ttk.Button(frame_busca, text="✕ Limpar", width=10, 
                   command=self.limpar_busca).pack(side=tk.LEFT, padx=3)
        
        # === FRAME DE AÇÕES ===
        frame_acoes = ttk.Frame(main_frame)
        frame_acoes.pack(fill=tk.X, pady=5)
        
        # Botões de ação
        ttk.Button(frame_acoes, text="📋 Copiar (Ctrl+C)", 
                   command=self.copiar_para_clipboard).pack(side=tk.LEFT, padx=3)
        ttk.Button(frame_acoes, text=" Atualizar", 
                   command=self.atualizar_lista).pack(side=tk.LEFT, padx=3)
        
        # Contador de resultados
        self.label_contador = ttk.Label(frame_acoes, text="", font=("Arial", 9))
        self.label_contador.pack(side=tk.RIGHT, padx=10)
        
        # === FRAME DA TABELA ===
        frame_tabela = ttk.Frame(main_frame)
        frame_tabela.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Colunas da tabela
        colunas = ("arquivo", "tipo", "potencia", "modulos")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=15)
        
        # Configurar colunas
        self.tree.heading("arquivo", text="📄 Arquivo", command=lambda: self.ordenar_coluna("arquivo"))
        self.tree.heading("tipo", text="⚡ Tipo", command=lambda: self.ordenar_coluna("tipo"))
        self.tree.heading("potencia", text="🔌 Potência", command=lambda: self.ordenar_coluna("potencia"))
        self.tree.heading("modulos", text="🔲 Módulos", command=lambda: self.ordenar_coluna("modulos"))
        
        self.tree.column("arquivo", width=350, minwidth=200)
        self.tree.column("tipo", width=100, minwidth=80)
        self.tree.column("potencia", width=100, minwidth=60)
        self.tree.column("modulos", width=100, minwidth=60)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Layout da tabela
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)
        
        # === STATUS BAR ===
        self.frame_status = ttk.Frame(main_frame)
        self.frame_status.pack(fill=tk.X, pady=(5, 0))
        
        self.label_status = ttk.Label(self.frame_status, text="", font=("Arial", 9))
        self.label_status.pack(side=tk.LEFT)
        
        self.label_pasta = ttk.Label(self.frame_status, text=f"📂 {PASTA_DWGS}", 
                                     font=("Arial", 8), foreground="gray")
        self.label_pasta.pack(side=tk.RIGHT)
        
        # === BINDINGS ===
        self.tree.bind("<Double-1>", self.copiar_para_clipboard)
        self.tree.bind("<Button-3>", self.menu_contexto)
        self.entrada.bind("<KeyRelease>", self.buscar_arquivos)
        self.combo_filtro.bind("<<ComboboxSelected>>", self.buscar_arquivos)
    
    def configurar_atalhos(self):
        """Configura atalhos de teclado"""
        self.root.bind("<Control-c>", self.copiar_para_clipboard)
        self.root.bind("<Control-C>", self.copiar_para_clipboard)
        self.root.bind("<Escape>", lambda e: self.limpar_busca())
        self.root.bind("<F5>", lambda e: self.atualizar_lista())
        self.root.bind("<Return>", self.copiar_para_clipboard)
    
    def carregar_arquivos(self):
        """Carrega lista de arquivos DWG da pasta ou Firebase"""
        self.arquivos_cache = []
        
        # Verificar se está usando Firebase
        if self.usando_firebase and self.firebase_sync:
            try:
                # Listar arquivos do Firebase
                arquivos_firebase = self.firebase_sync.list_files()
                
                for arq_info in arquivos_firebase:
                    info = self.extrair_info(arq_info['nome'])
                    info['firebase'] = True
                    info['caminho_remoto'] = arq_info['caminho']
                    self.arquivos_cache.append(info)
                
                self.mostrar_status(f"✓ {len(self.arquivos_cache)} arquivos (Firebase Cloud)", "green")
                return
            except Exception as e:
                self.mostrar_status(f"⚠ Erro Firebase, usando local: {str(e)[:30]}", "orange")
        
        # Modo local (fallback)
        if not os.path.exists(PASTA_DWGS):
            self.mostrar_status(f"⚠ Pasta não encontrada: {PASTA_DWGS}", "red")
            return
        
        try:
            for arquivo in os.listdir(PASTA_DWGS):
                if arquivo.lower().endswith(".dwg") and not arquivo.endswith(".bak"):
                    info = self.extrair_info(arquivo)
                    info['firebase'] = False
                    self.arquivos_cache.append(info)
            
            self.mostrar_status(f"✓ {len(self.arquivos_cache)} arquivos carregados (Local)", "green")
        except Exception as e:
            self.mostrar_status(f"✗ Erro ao carregar: {e}", "red")
    
    def extrair_info(self, nome_arquivo):
        """Extrai informações do nome do arquivo"""
        nome_lower = nome_arquivo.lower()
        
        # Identificar tipo
        tipo = "Indefinido"
        if any(k in nome_lower for k in ['trafo', 'transformador', 'cabine']):
            tipo = "Trafo"
        elif any(k in nome_lower for k in ['rural']):
            tipo = "Rural"
        elif nome_lower.startswith('tri') or any(k in nome_lower for k in ['3f', 'trifasico', 'trifásico', '380v']):
            tipo = "Trifásico"
        elif nome_lower.startswith('bi') or any(k in nome_lower for k in ['2f', 'bifasico', 'bifásico']):
            tipo = "Bifásico"
        
        # Extrair potência (números seguidos de kW ou kWp, ou padrão SIW seguido de número)
        potencia = ""
        # Padrão: SIW200G 10,5 ou SIW400G 37,5
        match = re.search(r'SIW\d+[GH]?\s*(\d+[,.]?\d*)', nome_arquivo, re.IGNORECASE)
        if match:
            potencia = match.group(1).replace(',', '.') + " kW"
        
        # Extrair quantidade de módulos (número antes de TW, TRINA, JA, ASTRO)
        modulos = ""
        match = re.search(r'[-\s](\d+)\s*(TW|TRINA|JA|ASTRO)', nome_arquivo, re.IGNORECASE)
        if match:
            modulos = match.group(1) + " mód"
        
        return {
            "arquivo": nome_arquivo,
            "tipo": tipo,
            "potencia": potencia,
            "modulos": modulos
        }
    
    def buscar_arquivos(self, event=None):
        """Busca arquivos com base nos filtros"""
        termo = self.entrada.get().strip().lower()
        tipo_filtro = self.combo_filtro.get()
        
        # Limpar tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filtrar arquivos
        resultados = []
        termos = termo.split()  # Suporta múltiplos termos
        
        for info in self.arquivos_cache:
            arquivo_lower = info["arquivo"].lower()
            
            # Verificar se todos os termos estão no nome
            if termos:
                if not all(t in arquivo_lower for t in termos):
                    continue
            
            # Verificar filtro de tipo
            if tipo_filtro != "Todos" and info["tipo"] != tipo_filtro:
                continue
            
            resultados.append(info)
        
        # Inserir na tabela
        for info in resultados:
            self.tree.insert("", tk.END, values=(
                info["arquivo"], 
                info["tipo"], 
                info["potencia"], 
                info["modulos"]
            ))
        
        # Atualizar contador
        total = len(self.arquivos_cache)
        encontrados = len(resultados)
        self.label_contador.config(text=f"📊 {encontrados} de {total} projetos")
        
        # Selecionar primeiro item se houver resultados
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])
    
    def ordenar_coluna(self, coluna):
        """Ordena a tabela por coluna clicada"""
        # Alternar ordem
        if self.ordem_atual["coluna"] == coluna:
            self.ordem_atual["reverso"] = not self.ordem_atual["reverso"]
        else:
            self.ordem_atual["coluna"] = coluna
            self.ordem_atual["reverso"] = False
        
        # Obter dados
        dados = [(self.tree.set(item, coluna), item) for item in self.tree.get_children()]
        
        # Ordenar
        dados.sort(key=lambda x: x[0].lower(), reverse=self.ordem_atual["reverso"])
        
        # Reorganizar
        for index, (val, item) in enumerate(dados):
            self.tree.move(item, "", index)
    
    def limpar_busca(self):
        """Limpa o campo de busca e reseta filtros"""
        self.entrada.delete(0, tk.END)
        self.combo_filtro.set("Todos")
        self.buscar_arquivos()
        self.entrada.focus_set()
    
    def atualizar_lista(self):
        """Recarrega a lista de arquivos"""
        if self.usando_firebase and self.firebase_sync:
            self.mostrar_status("🔄 Sincronizando...", "blue")
            
            # Sincronizar em thread separada
            def sync_and_reload():
                try:
                    self.firebase_sync.download_all()
                    self.root.after(0, self._atualizar_interface)
                except Exception as e:
                    self.root.after(0, lambda: self.mostrar_status(f"✗ Erro: {str(e)[:30]}", "red"))
            
            threading.Thread(target=sync_and_reload, daemon=True).start()
        else:
            self._atualizar_interface()
    
    def _atualizar_interface(self):
        """Atualiza interface após sincronização"""
        self.carregar_arquivos()
        self.buscar_arquivos()
        self.mostrar_status("✓ Lista atualizada", "green")
    
    def mostrar_status(self, mensagem, cor="black"):
        """Mostra mensagem de status temporária"""
        cores = {"green": "#228B22", "red": "#DC143C", "blue": "#4169E1", 
                 "orange": "#FF8C00", "black": "#000000"}
        self.label_status.config(text=mensagem, foreground=cores.get(cor, cor))
        self.root.after(4000, lambda: self.label_status.config(text=""))
    
    def obter_arquivo_selecionado(self):
        """Retorna o arquivo selecionado ou None"""
        selecao = self.tree.selection()
        if not selecao:
            self.mostrar_status("⚠ Selecione um arquivo primeiro", "orange")
            return None
        
        item = self.tree.item(selecao[0])
        return item['values'][0]
    
    def copiar_para_clipboard(self, event=None):
        """Copia o arquivo selecionado para a área de transferência"""
        arquivo = self.obter_arquivo_selecionado()
        if not arquivo:
            return
        
        nome_copia = CONFIG.get("nome_arquivo_copia", "PROJETO.dwg")
        
        try:
            # Verificar se é arquivo do Firebase
            info_arquivo = next((info for info in self.arquivos_cache if info['arquivo'] == arquivo), None)
            
            if info_arquivo and info_arquivo.get('firebase', False):
                # Baixar do Firebase se necessário
                self.mostrar_status("🔍 Verificando arquivo...", "blue")
                
                result = self.firebase_sync.download_file(info_arquivo['caminho_remoto'])
                if not result:
                    self.mostrar_status("✗ Erro ao obter arquivo", "red")
                    return
                
                # download_file agora retorna tupla (path, status)
                if isinstance(result, tuple):
                    caminho_local, status = result
                    if status == 'cached':
                        self.mostrar_status("✓ Usando cache local", "green")
                    else:
                        self.mostrar_status("✓ Arquivo baixado", "green")
                else:
                    caminho_local = result
                
                caminho_arquivo = caminho_local
            else:
                # Arquivo local
                caminho_arquivo = os.path.join(PASTA_DWGS, arquivo)
            
            # Copiar para pasta temporária
            pasta_temp = tempfile.gettempdir()
            destino = os.path.join(pasta_temp, nome_copia)
            shutil.copy2(caminho_arquivo, destino)
            
            if sys.platform == "win32" and HAS_WIN32:
                # Windows: clipboard com arquivo
                arquivos_str = destino + '\0'
                arquivos_bytes = arquivos_str.encode('utf-16le') + b'\0\0'
                dropfiles_struct = struct.pack("IiiII", 20, 0, 0, 0, 1)
                data = dropfiles_struct + arquivos_bytes
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(CF_HDROP, data)
                win32clipboard.CloseClipboard()
                
                self.mostrar_status(f"✓ Copiado como {nome_copia}", "green")
            else:
                # Linux/Mac: copiar caminho
                try:
                    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                              stdin=subprocess.PIPE)
                    process.communicate(destino.encode('utf-8'))
                    self.mostrar_status(f"✓ Caminho copiado: {destino}", "green")
                except FileNotFoundError:
                    self.mostrar_status(f"✓ Arquivo em: {destino}", "blue")
        
        except Exception as e:
            self.mostrar_status(f"✗ Erro: {str(e)[:50]}", "red")
    
    def menu_contexto(self, event):
        """Mostra menu de contexto no clique direito"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📋 Copiar arquivo", command=self.copiar_para_clipboard)
        menu.add_separator()
        menu.add_command(label="🔄 Atualizar lista", command=self.atualizar_lista)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


class LoginWindow:
    """Janela de login para autenticação"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Banco de Projetos - Login")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Centralizar janela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")
        
        self.auth_manager = AuthManager()
        self.authenticated = False
        self.username = None
        
        self.criar_interface()
        
        # Focar no campo de usuário
        self.entry_user.focus_set()
    
    def criar_interface(self):
        """Cria interface de login"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(
            main_frame,
            text="🔍 Banco de Projetos DWG",
            font=("Segoe UI", 16, "bold")
        )
        titulo.pack(pady=(0, 10))
        
        subtitulo = ttk.Label(
            main_frame,
            text="Autenticação Necessária",
            font=("Segoe UI", 10)
        )
        subtitulo.pack(pady=(0, 30))
        
        # Frame de campos
        campos_frame = ttk.Frame(main_frame)
        campos_frame.pack(fill=tk.X, pady=10)
        
        # Usuário
        ttk.Label(campos_frame, text="Usuário:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.entry_user = ttk.Entry(campos_frame, font=("Segoe UI", 11))
        self.entry_user.pack(fill=tk.X, pady=(5, 15))
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus_set())
        
        # Senha
        ttk.Label(campos_frame, text="Senha:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self.entry_pass = ttk.Entry(campos_frame, font=("Segoe UI", 11), show="•")
        self.entry_pass.pack(fill=tk.X, pady=(5, 20))
        self.entry_pass.bind("<Return>", lambda e: self.fazer_login())
        
        # Botão de login
        btn_login = ttk.Button(
            campos_frame,
            text="🔓 Entrar",
            command=self.fazer_login
        )
        btn_login.pack(fill=tk.X, ipady=8)
        
        # Label de status
        self.label_status = ttk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9),
            foreground="red"
        )
        self.label_status.pack(pady=(10, 0))
        
        # Rodapé com dica
        rodape = ttk.Label(
            main_frame,
            text="Usuário padrão: admin / admin",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        rodape.pack(side=tk.BOTTOM, pady=(20, 0))
    
    def fazer_login(self):
        """Realiza autenticação"""
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()
        
        if not username or not password:
            self.mostrar_erro("Preencha usuário e senha")
            return
        
        if self.auth_manager.authenticate(username, password):
            self.authenticated = True
            self.username = username
            self.root.destroy()
        else:
            self.mostrar_erro("Usuário ou senha incorretos")
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.focus_set()
    
    def mostrar_erro(self, mensagem):
        """Mostra mensagem de erro"""
        self.label_status.config(text=f"❌ {mensagem}")
        self.root.after(3000, lambda: self.label_status.config(text=""))


def main():
    """Função principal"""
    # Verificar se autenticação está disponível
    if not AUTH_AVAILABLE:
        messagebox.showerror(
            "Erro",
            "Módulo de autenticação não disponível.\n"
            "Verifique se o arquivo auth.py existe."
        )
        return
    
    # Janela de login
    login_root = tk.Tk()
    login_window = LoginWindow(login_root)
    login_root.mainloop()
    
    # Verificar se foi autenticado
    if not login_window.authenticated:
        return
    
    # Abrir aplicação principal
    username = login_window.username
    root = tk.Tk()
    app = BuscaDWG(root, username)
    root.mainloop()


if __name__ == "__main__":
    main()
