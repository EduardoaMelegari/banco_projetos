#!/usr/bin/env python3
"""
Script de build para criar executável .exe do Banco de Projetos DWG

Usa PyInstaller para gerar um executável Windows portátil
"""

import os
import sys
import shutil
import subprocess


def verificar_pyinstaller():
    """Verifica se PyInstaller está instalado"""
    try:
        import PyInstaller
        print("✓ PyInstaller instalado")
        return True
    except ImportError:
        print("❌ PyInstaller não encontrado")
        print("\nInstale com: pip install pyinstaller")
        return False


def limpar_build():
    """Limpa diretórios de build anteriores"""
    print("\n🧹 Limpando builds anteriores...")
    
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  ✓ Removido: {dir_name}/")
            except PermissionError:
                print(f"  ⚠️ Não foi possível remover {dir_name}/ (permissão negada)")
            except Exception as e:
                print(f"  ⚠️ Erro ao remover {dir_name}/: {e}")
    
    # Remover arquivos .spec antigos
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            try:
                os.remove(file)
                print(f"  ✓ Removido: {file}")
            except Exception as e:
                print(f"  ⚠️ Erro ao remover {file}: {e}")


def criar_executavel():
    """Cria o executável usando PyInstaller"""
    print("\n🔨 Compilando aplicação...\n")
    
    comando = [
        'pyinstaller',
        '--name=BancoProjetosDWG',
        '--onefile',  # Gera um único arquivo .exe
        '--windowed',  # Sem console (apenas GUI)
        '--icon=NONE',  # Adicione um ícone .ico se tiver
        '--add-data=firebase_sync.py;.',
        '--add-data=auth.py;.',
        '--hidden-import=firebase_admin',
        '--hidden-import=google.cloud',
        '--hidden-import=dotenv',
        '--noconfirm',
        'banco_projetos.py'
    ]
    
    try:
        result = subprocess.run(comando, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao compilar: {e}")
        return False


def criar_pasta_distribuicao():
    """Cria pasta com executável e arquivos necessários"""
    print("\n📦 Criando pasta de distribuição...\n")
    
    # Criar pasta dist_final
    dist_dir = 'BancoProjetosDWG_Portable'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copiar executável
    exe_src = 'dist/BancoProjetosDWG.exe'
    if os.path.exists(exe_src):
        shutil.copy2(exe_src, dist_dir)
        print(f"  ✓ {exe_src} → {dist_dir}/")
    
    # Criar arquivo .env.example
    env_example = os.path.join(dist_dir, '.env.example')
    with open(env_example, 'w') as f:
        f.write("""# Configurações Firebase Storage
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_BUCKET=banco-projetos-dwg.firebasestorage.app

# Pasta local de cache (deixe vazio para usar temp)
LOCAL_CACHE_DIR=

# Sincronização automática ao iniciar (true/false)
AUTO_SYNC_ON_START=true

# Intervalo de sincronização em segundos (0 = desabilitado)
SYNC_INTERVAL=300
""")
    print(f"  ✓ Criado: {env_example}")
    
    # Criar README de instalação
    readme_path = os.path.join(dist_dir, 'LEIA-ME.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""═══════════════════════════════════════════════════════════
  BANCO DE PROJETOS DWG - VERSÃO PORTÁTIL
═══════════════════════════════════════════════════════════

📋 CONTEÚDO:
  • BancoProjetosDWG.exe      - Aplicação executável
  • .env.example              - Modelo de configuração
  • LEIA-ME.txt               - Este arquivo

🚀 PRIMEIRA EXECUÇÃO:

1. COPIE o arquivo de credenciais Firebase:
   → firebase-credentials.json (obtido do Firebase Console)
   → Cole nesta mesma pasta

2. COPIE e RENOMEIE .env.example para .env:
   → Edite o arquivo .env
   → Configure o FIREBASE_BUCKET correto

3. EXECUTE BancoProjetosDWG.exe:
   → Login: admin
   → Senha: admin
   → IMPORTANTE: Altere a senha após primeiro acesso!

📁 ESTRUTURA APÓS CONFIGURAÇÃO:
  BancoProjetosDWG_Portable/
  ├── BancoProjetosDWG.exe          ← Executável principal
  ├── firebase-credentials.json     ← Suas credenciais
  ├── .env                          ← Sua configuração
  ├── .env.example                  ← Modelo
  ├── users.json                    ← Criado automaticamente
  ├── app_config.json               ← Criado automaticamente
  └── LEIA-ME.txt                   ← Este arquivo

⚙️ CONFIGURAÇÃO:

  Arquivo .env:
    FIREBASE_BUCKET=seu-bucket.firebasestorage.app
    AUTO_SYNC_ON_START=true

  Onde encontrar o bucket:
    Firebase Console > Storage > Nome do bucket

🔐 GERENCIAR USUÁRIOS:

  Para adicionar/remover usuários ou alterar senhas:
  1. Abra um terminal/CMD nesta pasta
  2. Execute:
     
     python -c "from auth import AuthManager; auth = AuthManager(); 
     auth.add_user('usuario', 'senha123', 'Nome Completo')"

  Ou use o script manage_users.py (se disponível)

💡 DICAS:

  • Cache dos arquivos fica em: %TEMP%\\banco_projetos_dwg
  • Primeira sincronização pode demorar (baixa todos os DWGs)
  • Próximas execuções são rápidas (só baixa novos/modificados)
  • Funciona offline após primeira sincronização

🆘 PROBLEMAS COMUNS:

  ❌ "Could not load credentials"
     → Verifique se firebase-credentials.json está na pasta
     → Verifique se o nome do arquivo está correto

  ❌ "Storage bucket not found"
     → Edite .env e corrija o FIREBASE_BUCKET
     → Veja o nome correto no Firebase Console > Storage

  ❌ Aplicação não abre
     → Execute pelo CMD para ver erros
     → Verifique antivírus (pode bloquear .exe)

📞 SUPORTE:

  Repositório: https://github.com/EduardoaMelegari/banco_projetos
  Firebase: https://console.firebase.google.com/

═══════════════════════════════════════════════════════════
Versão: 1.0 | 2026 | Firebase Cloud Edition
═══════════════════════════════════════════════════════════
""")
    print(f"  ✓ Criado: {readme_path}")
    
    print(f"\n✓ Pasta criada: {dist_dir}/")
    return dist_dir


def main():
    print("=" * 60)
    print("  BUILD - BANCO DE PROJETOS DWG")
    print("=" * 60)
    
    # Verificar PyInstaller
    if not verificar_pyinstaller():
        return 1
    
    # Limpar builds anteriores
    limpar_build()
    
    # Criar executável
    if not criar_executavel():
        print("\n❌ Falha ao criar executável")
        return 1
    
    # Criar pasta de distribuição
    dist_dir = criar_pasta_distribuicao()
    
    print("\n" + "=" * 60)
    print("  ✅ BUILD CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print(f"\n📦 Arquivos em: {dist_dir}/")
    print("\n📋 Próximos passos:")
    print(f"  1. Copie a pasta '{dist_dir}' para onde quiser")
    print("  2. Adicione firebase-credentials.json")
    print("  3. Configure o .env")
    print("  4. Execute BancoProjetosDWG.exe")
    print("\n✓ O executável é PORTÁTIL - não precisa instalação!")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
