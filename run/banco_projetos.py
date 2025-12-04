import os
import tkinter as tk
from tkinter import messagebox, Scrollbar, ttk
import struct
import tempfile
import shutil
import subprocess
import sys

# Importações específicas do Windows (só carrega se estiver no Windows)
if sys.platform == "win32":
    import win32clipboard
    from win32con import CF_HDROP

# ======= CONFIGURAÇÕES =======
# Determina o caminho da pasta CONTROLE relativo ao script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_DWGS = os.path.join(os.path.dirname(SCRIPT_DIR), "CONTROLE")

# Fallback para Windows se o caminho acima não existir
if not os.path.exists(PASTA_DWGS):
    PASTA_DWGS = r"C:\Projetos Solturi\assinatura\CONTROLE"
# =============================

def identificar_tipo(nome_arquivo):
    """Identifica o tipo do arquivo baseado no nome"""
    nome_lower = nome_arquivo.lower()
    
    # Palavras-chave para identificar cada tipo
    trifasico_keys = ['3f', 'trifasico', 'trifásico', '380v', '220v trifasico', 'tri']
    bifasico_keys = ['2f', 'bifasico', 'bifásico', '220v bifasico', '220v bi', 'bi']
    trafo_keys = ['trafo', 'transformador', 'transf', 'cabine', 'subestacao', 'subestação']
    
    # Verificar trafo primeiro (mais específico)
    for key in trafo_keys:
        if key in nome_lower:
            return "Trafo"
    
    # Verificar trifásico
    for key in trifasico_keys:
        if key in nome_lower:
            return "Trifásico"
    
    # Verificar bifásico
    for key in bifasico_keys:
        if key in nome_lower:
            return "Bifásico"
    
    # Se não identificar, retorna "Indefinido"
    return "Indefinido"

def buscar_arquivos(*args):
    termo = entrada.get().strip().lower()
    
    # Limpar a árvore
    for item in tree.get_children():
        tree.delete(item)

    if not termo:
        return

    for arquivo in os.listdir(PASTA_DWGS):
        if termo in arquivo.lower() and arquivo.lower().endswith(".dwg"):
            tipo = identificar_tipo(arquivo)
            tree.insert("", tk.END, values=(arquivo, tipo))

def mostrar_status(mensagem, cor="green"):
    """Mostra uma mensagem de status temporária"""
    label_status.config(text=mensagem, fg=cor)
    janela.after(3000, lambda: label_status.config(text=""))  # Remove após 3 segundos

def copiar_para_clipboard(event=None):
    selecao = tree.selection()
    if not selecao:
        return
    
    item = tree.item(selecao[0])
    arquivo = item['values'][0]
    caminho_arquivo = os.path.join(PASTA_DWGS, arquivo)

    try:
        # Pasta temporária do sistema
        pasta_temp = tempfile.gettempdir()
        destino = os.path.join(pasta_temp, "PROJETO.dwg")

        # Copiar o arquivo para a pasta temporária com novo nome
        shutil.copy2(caminho_arquivo, destino)

        if sys.platform == "win32":
            # Windows: usar win32clipboard
            # Preparar dados para a área de transferência no formato CF_HDROP
            arquivos_str = destino + '\0'  # separador único
            arquivos_bytes = arquivos_str.encode('utf-16le') + b'\0\0'  # terminador duplo

            # Estrutura DROPFILES
            dropfiles_struct = struct.pack("IiiII", 20, 0, 0, 0, 1)

            data = dropfiles_struct + arquivos_bytes

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(CF_HDROP, data)
            win32clipboard.CloseClipboard()
            
            mostrar_status("✓ Arquivo copiado como PROJETO.dwg")
        else:
            # Linux: copiar o caminho para a área de transferência usando xclip
            try:
                # Tenta usar xclip para copiar o caminho do arquivo
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                          stdin=subprocess.PIPE)
                process.communicate(destino.encode('utf-8'))
                mostrar_status(f"✓ Arquivo copiado para {destino}")
            except FileNotFoundError:
                # Se xclip não estiver instalado, apenas mostrar o caminho
                mostrar_status(f"✓ Copiado para: {destino}", "blue")
        
    except Exception as e:
        mostrar_status(f"✗ Erro ao copiar: {str(e)[:50]}...", "red")

def abrir_pasta():
    selecao = tree.selection()
    if not selecao:
        mostrar_status("⚠ Selecione um arquivo primeiro", "orange")
        return
    
    item = tree.item(selecao[0])
    arquivo = item['values'][0]
    caminho_arquivo = os.path.join(PASTA_DWGS, arquivo)
    
    try:
        # Abrir o Explorer do Windows e selecionar o arquivo
        if sys.platform == "win32":
            subprocess.run(['explorer', '/select,', caminho_arquivo])
        else:
            # Para outros sistemas operacionais, abrir apenas a pasta
            pasta = os.path.dirname(caminho_arquivo)
            if sys.platform == "darwin":  # macOS
                subprocess.run(['open', pasta])
            else:  # Linux
                subprocess.run(['xdg-open', pasta])
        
        mostrar_status("📁 Pasta aberta")
        
    except Exception as e:
        mostrar_status(f"✗ Erro ao abrir pasta: {str(e)[:40]}...", "red")

def menu_contexto(event):
    # Verificar se clicou em um item
    item = tree.identify_row(event.y)
    if item:
        tree.selection_set(item)
        
        # Criar menu de contexto
        menu = tk.Menu(janela, tearoff=0)
        menu.add_command(label="Copiar arquivo", command=copiar_para_clipboard)
        menu.add_command(label="Abrir pasta", command=abrir_pasta)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

def filtrar_por_tipo(event=None):
    """Filtrar resultados por tipo selecionado"""
    buscar_arquivos()  # Refazer a busca
    
    tipo_selecionado = combo_filtro.get()
    if tipo_selecionado == "Todos":
        return
    
    # Remover itens que não correspondem ao filtro
    for item in tree.get_children():
        valores = tree.item(item)['values']
        if len(valores) > 1 and valores[1] != tipo_selecionado:
            tree.delete(item)

# ======== INTERFACE =========
janela = tk.Tk()
janela.title("Busca DWG")
janela.geometry("600x400")  # Menor largura e altura

# Frame de busca
frame_busca = tk.Frame(janela)
frame_busca.pack(pady=5)  # Menor espaçamento

tk.Label(frame_busca, text="Nome:").pack(side=tk.LEFT, padx=3)
entrada = tk.Entry(frame_busca, width=20)  # Campo menor
entrada.pack(side=tk.LEFT, padx=3)

# Filtro por tipo
tk.Label(frame_busca, text="Tipo:").pack(side=tk.LEFT, padx=3)
combo_filtro = ttk.Combobox(frame_busca,
                            values=["Todos", "Bifásico", "Trifásico", "Trafo", "Indefinido"],
                            state="readonly", width=10)
combo_filtro.set("Todos")
combo_filtro.pack(side=tk.LEFT, padx=3)

# Botões
frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=3)
tk.Button(frame_botoes, text="Copiar", width=10, command=copiar_para_clipboard).pack(side=tk.LEFT, padx=3)
tk.Button(frame_botoes, text="Abrir", width=10, command=abrir_pasta).pack(side=tk.LEFT, padx=3)

# Status
label_status = tk.Label(janela, text="", font=("Arial", 8))
label_status.pack(pady=1)

# Tabela
frame_tabela = tk.Frame(janela)
frame_tabela.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

tree = ttk.Treeview(frame_tabela, columns=("Arquivo", "Tipo"), show="headings", height=10)
tree.heading("Arquivo", text="Arquivo")
tree.heading("Tipo", text="Tipo")
tree.column("Arquivo", width=380)
tree.column("Tipo", width=100)

scrollbar_tree = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar_tree.set)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)

# Eventos
tree.bind("<Double-1>", copiar_para_clipboard)
tree.bind("<Button-3>", menu_contexto)  # Clique direito
entrada.bind("<KeyRelease>", buscar_arquivos)
combo_filtro.bind("<<ComboboxSelected>>", filtrar_por_tipo)

# Instruções para o usuário
frame_instrucoes = tk.Frame(janela)
frame_instrucoes.pack(pady=5)

instrucoes = tk.Label(frame_instrucoes, 
                     text="• Duplo clique: Copiar arquivo • Clique direito: Menu com opções • Use o filtro para mostrar apenas um tipo específico",
                     justify=tk.CENTER, font=("Arial", 8), fg="gray")
instrucoes.pack()

# Frame de legenda
frame_legenda = tk.Frame(janela)
frame_legenda.pack(pady=2)

legenda = tk.Label(frame_legenda, 
                  text="Classificação automática baseada em palavras-chave: Bifásico (2f, bi, bifásico) • Trifásico (3f, tri, trifásico) • Trafo (trafo, transformador, cabine)",
                  justify=tk.CENTER, font=("Arial", 7), fg="blue")
legenda.pack()

janela.mainloop()