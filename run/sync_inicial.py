#!/usr/bin/env python3
"""
Script de sincronização inicial de arquivos DWG com Firebase Storage

Este script faz o upload inicial de todos os arquivos .dwg da pasta CONTROLE
para o Firebase Storage. Use apenas uma vez ou quando quiser atualizar
todos os arquivos na nuvem.

Uso:
    python sync_inicial.py              # Upload normal
    python sync_inicial.py --dry-run    # Teste (sem fazer upload real)
    python sync_inicial.py --force      # Forçar upload de todos
"""

import os
import sys
import argparse
from firebase_sync import FirebaseSync


def main():
    parser = argparse.ArgumentParser(
        description='Sincroniza arquivos DWG locais com Firebase Storage'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula upload sem fazer alterações reais'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Força upload de todos os arquivos, mesmo que já existam'
    )
    parser.add_argument(
        '--folder',
        default='../CONTROLE',
        help='Pasta com arquivos DWG (padrão: ../CONTROLE)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔥 SINCRONIZAÇÃO INICIAL COM FIREBASE STORAGE")
    print("=" * 60)
    
    # Verificar se pasta existe
    pasta_controle = os.path.abspath(args.folder)
    if not os.path.exists(pasta_controle):
        print(f"\n❌ Pasta não encontrada: {pasta_controle}")
        print("\nTente especificar o caminho correto:")
        print("  python sync_inicial.py --folder /caminho/para/CONTROLE")
        return 1
    
    # Contar arquivos DWG
    arquivos_dwg = [f for f in os.listdir(pasta_controle) 
                    if f.lower().endswith('.dwg') and not f.endswith('.bak')]
    
    print(f"\n📂 Pasta: {pasta_controle}")
    print(f"📄 Arquivos DWG encontrados: {len(arquivos_dwg)}")
    
    if not arquivos_dwg:
        print("\n⚠️ Nenhum arquivo DWG encontrado!")
        return 1
    
    # Mostrar alguns exemplos
    print("\nExemplos de arquivos:")
    for arquivo in arquivos_dwg[:5]:
        print(f"  • {arquivo}")
    if len(arquivos_dwg) > 5:
        print(f"  ... e mais {len(arquivos_dwg) - 5} arquivos")
    
    # Modo dry-run
    if args.dry_run:
        print("\n🔍 MODO DE TESTE (dry-run)")
        print("Nenhum arquivo será realmente enviado.")
        print("\nPara fazer upload real, execute sem --dry-run:")
        print("  python sync_inicial.py")
        return 0
    
    # Confirmar
    print("\n" + "=" * 60)
    print("⚠️  ATENÇÃO:")
    print("   Isso fará upload de todos os arquivos DWG para Firebase Storage.")
    if args.force:
        print("   Modo --force: sobrescreverá arquivos existentes na nuvem.")
    else:
        print("   Apenas arquivos novos/modificados serão enviados.")
    print("=" * 60)
    
    resposta = input("\nDeseja continuar? (sim/não): ").strip().lower()
    if resposta not in ['sim', 's', 'yes', 'y']:
        print("\n❌ Operação cancelada pelo usuário.")
        return 0
    
    # Inicializar Firebase
    try:
        print("\n🔄 Inicializando conexão com Firebase...")
        sync = FirebaseSync()
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao Firebase:")
        print(f"   {e}")
        print("\nVerifique:")
        print("  1. Arquivo firebase-credentials.json existe")
        print("  2. Arquivo .env está configurado corretamente")
        print("  3. FIREBASE_BUCKET no .env está correto")
        return 1
    
    # Fazer sincronização
    print("\n" + "=" * 60)
    print("🚀 INICIANDO UPLOAD")
    print("=" * 60)
    
    try:
        stats = sync.sync_folder(pasta_controle, "CONTROLE/")
        
        print("\n" + "=" * 60)
        print("✅ SINCRONIZAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print(f"  ✓ {stats['uploaded']} arquivos enviados")
        print(f"  ⊘ {stats['skipped']} já estavam atualizados")
        if stats['failed'] > 0:
            print(f"  ✗ {stats['failed']} falharam")
        print("=" * 60)
        
        # Listar arquivos no Firebase
        print("\n📦 Arquivos na nuvem:")
        arquivos_cloud = sync.list_files()
        print(f"   Total: {len(arquivos_cloud)} arquivos")
        
        # Calcular tamanho total
        tamanho_total = sum(a['tamanho'] for a in arquivos_cloud)
        tamanho_mb = tamanho_total / (1024 * 1024)
        print(f"   Espaço usado: {tamanho_mb:.2f} MB")
        
        print("\n✓ Agora você pode usar a aplicação GUI normalmente!")
        print("  Os arquivos serão sincronizados automaticamente da nuvem.\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro durante sincronização:")
        print(f"   {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
