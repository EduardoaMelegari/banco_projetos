"""
Módulo de sincronização de arquivos DWG com Firebase Storage

Este módulo gerencia:
- Upload e download de arquivos DWG para/do Firebase
- Cache local de arquivos para acesso offline
- Sincronização automática periódica
- Listagem de arquivos disponíveis na nuvem
"""

import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

try:
    import firebase_admin
    from firebase_admin import credentials, storage
    from dotenv import load_dotenv
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase não disponível. Instale: pip install firebase-admin python-dotenv")


class FirebaseSync:
    """Gerenciador de sincronização com Firebase Storage"""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa o gerenciador Firebase
        
        Args:
            config_path: Caminho para o arquivo .env (opcional)
        """
        self.initialized = False
        self.bucket = None
        self.cache_dir = None
        self.sync_thread = None
        self.running = False
        
        if not FIREBASE_AVAILABLE:
            raise ImportError("Firebase não está instalado. Execute: pip install firebase-admin python-dotenv")
        
        # Carregar variáveis de ambiente
        if config_path and os.path.exists(config_path):
            load_dotenv(config_path)
        else:
            load_dotenv()  # Tenta carregar do diretório atual
        
        # Inicializar Firebase
        self._initialize_firebase()
        
        # Configurar cache local
        self._setup_cache()
    
    def _initialize_firebase(self):
        """Inicializa conexão com Firebase"""
        try:
            # Buscar configurações
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
            bucket_name = os.getenv('FIREBASE_BUCKET')
            
            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"❌ Arquivo de credenciais não encontrado: {cred_path}\n"
                    "Configure o arquivo .env e baixe as credenciais do Firebase Console"
                )
            
            if not bucket_name:
                raise ValueError(
                    "❌ FIREBASE_BUCKET não configurado no .env\n"
                    "Adicione: FIREBASE_BUCKET=seu-projeto.appspot.com"
                )
            
            # Inicializar Firebase (se já não foi inicializado)
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                })
            
            self.bucket = storage.bucket()
            self.initialized = True
            print(f"✓ Conectado ao Firebase Storage: {bucket_name}")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")
            raise
    
    def _setup_cache(self):
        """Configura diretório de cache local"""
        cache_path = os.getenv('LOCAL_CACHE_DIR', '')
        
        if cache_path and cache_path.strip():
            self.cache_dir = Path(cache_path).resolve()
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Usar diretório temporário do sistema
            self.cache_dir = Path(tempfile.gettempdir()) / "banco_projetos_dwg"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Cache local: {self.cache_dir}")
    
    def list_files(self, prefix: str = "CONTROLE/") -> List[Dict[str, any]]:
        """
        Lista arquivos DWG disponíveis no Firebase
        
        Args:
            prefix: Prefixo para filtrar arquivos (pasta)
        
        Returns:
            Lista de dicionários com informações dos arquivos
        """
        if not self.initialized:
            return []
        
        try:
            arquivos = []
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            for blob in blobs:
                if blob.name.lower().endswith('.dwg'):
                    arquivos.append({
                        'nome': os.path.basename(blob.name),
                        'caminho': blob.name,
                        'tamanho': blob.size,
                        'atualizado': blob.updated.isoformat() if blob.updated else None,
                        'md5_hash': blob.md5_hash
                    })
            
            return arquivos
            
        except Exception as e:
            print(f"❌ Erro ao listar arquivos: {e}")
            return []
    
    def download_file(self, remote_path: str, force: bool = False, verbose: bool = True) -> Optional[str]:
        """
        Baixa arquivo do Firebase para cache local
        
        Args:
            remote_path: Caminho do arquivo no Firebase (ex: CONTROLE/arquivo.dwg)
            force: Forçar download mesmo se já existir no cache
            verbose: Mostrar mensagens de progresso
        
        Returns:
            Tupla (caminho_local, status) onde status é 'downloaded', 'cached' ou None se falhar
        """
        if not self.initialized:
            return None
        
        try:
            # Definir caminho local
            local_file = self.cache_dir / os.path.basename(remote_path)
            
            # Verificar se já existe no cache
            if local_file.exists() and not force:
                # Verificar se precisa atualizar
                blob = self.bucket.blob(remote_path)
                if blob.exists():
                    # Comparar hash MD5
                    local_md5 = self._calculate_md5(local_file)
                    if local_md5 == blob.md5_hash:
                        # Arquivo já está atualizado no cache
                        return (str(local_file), 'cached')
            
            # Download do arquivo
            blob = self.bucket.blob(remote_path)
            if not blob.exists():
                if verbose:
                    print(f"❌ Arquivo não encontrado no Firebase: {remote_path}")
                return None
            
            blob.download_to_filename(str(local_file))
            if verbose:
                print(f"⬇️ Baixado: {os.path.basename(remote_path)}")
            return (str(local_file), 'downloaded')
            
        except Exception as e:
            if verbose:
                print(f"❌ Erro ao baixar {remote_path}: {e}")
            return None
    
    def upload_file(self, local_path: str, remote_path: str = None) -> bool:
        """
        Faz upload de arquivo local para Firebase
        
        Args:
            local_path: Caminho do arquivo local
            remote_path: Caminho destino no Firebase (opcional, usa CONTROLE/nome.dwg)
        
        Returns:
            True se sucesso, False se falhar
        """
        if not self.initialized:
            return False
        
        try:
            if not os.path.exists(local_path):
                print(f"❌ Arquivo local não encontrado: {local_path}")
                return False
            
            # Definir caminho remoto
            if not remote_path:
                remote_path = f"CONTROLE/{os.path.basename(local_path)}"
            
            # Upload
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            print(f"✓ Upload: {os.path.basename(local_path)} → {remote_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao fazer upload de {local_path}: {e}")
            return False
    
    def sync_folder(self, local_folder: str, remote_prefix: str = "CONTROLE/") -> Dict[str, int]:
        """
        Sincroniza pasta local com Firebase (upload de novos/modificados)
        
        Args:
            local_folder: Pasta local com arquivos DWG
            remote_prefix: Prefixo no Firebase
        
        Returns:
            Dict com estatísticas: {'uploaded': n, 'skipped': n, 'failed': n}
        """
        stats = {'uploaded': 0, 'skipped': 0, 'failed': 0}
        
        if not os.path.exists(local_folder):
            print(f"❌ Pasta não encontrada: {local_folder}")
            return stats
        
        print(f"\n🔄 Sincronizando pasta: {local_folder}")
        print(f"   Destino Firebase: {remote_prefix}")
        
        # Listar arquivos locais
        local_files = [f for f in os.listdir(local_folder) 
                      if f.lower().endswith('.dwg')]
        
        # Listar arquivos remotos
        remote_files = {f['nome']: f for f in self.list_files(remote_prefix)}
        
        for filename in local_files:
            local_path = os.path.join(local_folder, filename)
            remote_path = f"{remote_prefix}{filename}"
            
            # Verificar se precisa upload
            needs_upload = True
            if filename in remote_files:
                local_md5 = self._calculate_md5(local_path)
                if local_md5 == remote_files[filename]['md5_hash']:
                    needs_upload = False
                    stats['skipped'] += 1
                    print(f"⊘ Igual: {filename}")
            
            if needs_upload:
                if self.upload_file(local_path, remote_path):
                    stats['uploaded'] += 1
                else:
                    stats['failed'] += 1
        
        print(f"\n✓ Sincronização completa:")
        print(f"  • {stats['uploaded']} enviados")
        print(f"  • {stats['skipped']} já atualizados")
        print(f"  • {stats['failed']} falharam")
        
        return stats
    
    def download_all(self, force: bool = False) -> Dict[str, int]:
        """
        Baixa todos os arquivos DWG do Firebase para cache local
        
        Args:
            force: Forçar download de todos (ignorar cache)
        
        Returns:
            Dicionário com estatísticas: {'downloaded': n, 'cached': n, 'failed': n}
        """
        arquivos = self.list_files()
        stats = {'downloaded': 0, 'cached': 0, 'failed': 0}
        
        print(f"\n🔍 Verificando {len(arquivos)} arquivos...")
        
        for arquivo in arquivos:
            result = self.download_file(arquivo['caminho'], force, verbose=False)
            if result:
                path, status = result
                if status == 'downloaded':
                    stats['downloaded'] += 1
                    print(f"  ⬇️ {arquivo['nome']}")
                elif status == 'cached':
                    stats['cached'] += 1
            else:
                stats['failed'] += 1
        
        # Mensagem resumida
        print()
        if stats['downloaded'] > 0:
            print(f"✓ {stats['downloaded']} novos baixados, {stats['cached']} já estavam atualizados")
        else:
            print(f"✓ Todos os {stats['cached']} arquivos já estão atualizados no cache")
        
        if stats['failed'] > 0:
            print(f"⚠ {stats['failed']} falharam")
        
        return stats
    
    def start_auto_sync(self, interval: int = 300):
        """
        Inicia sincronização automática em background
        
        Args:
            interval: Intervalo em segundos (padrão: 300 = 5 min)
        """
        if self.sync_thread and self.sync_thread.is_alive():
            print("⚠️ Sincronização automática já está rodando")
            return
        
        self.running = True
        self.sync_thread = threading.Thread(
            target=self._auto_sync_loop,
            args=(interval,),
            daemon=True
        )
        self.sync_thread.start()
        print(f"✓ Sincronização automática iniciada (intervalo: {interval}s)")
    
    def stop_auto_sync(self):
        """Para sincronização automática"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("✓ Sincronização automática parada")
    
    def _auto_sync_loop(self, interval: int):
        """Loop de sincronização automática (interno)"""
        while self.running:
            try:
                print(f"\n🔄 Sincronização automática: {datetime.now().strftime('%H:%M:%S')}")
                self.download_all()
            except Exception as e:
                print(f"❌ Erro na sincronização automática: {e}")
            
            # Aguardar intervalo
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _calculate_md5(self, file_path: str) -> str:
        """Calcula hash MD5 de um arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_cache_path(self, filename: str) -> str:
        """Retorna caminho no cache para um arquivo"""
        return str(self.cache_dir / filename)
    
    def clear_cache(self):
        """Limpa todo o cache local"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print("✓ Cache limpo")
        except Exception as e:
            print(f"❌ Erro ao limpar cache: {e}")


# Função auxiliar para teste
if __name__ == "__main__":
    print("🔥 Teste do Firebase Sync\n")
    
    try:
        # Inicializar
        sync = FirebaseSync()
        
        # Listar arquivos
        print("\n📂 Arquivos no Firebase:")
        arquivos = sync.list_files()
        for arq in arquivos[:5]:  # Mostrar apenas 5
            print(f"  • {arq['nome']} ({arq['tamanho']} bytes)")
        print(f"  ... total: {len(arquivos)} arquivos")
        
        # Testar download
        if arquivos:
            print("\n⬇️  Testando download...")
            path = sync.download_file(arquivos[0]['caminho'])
            if path:
                print(f"✓ Arquivo baixado para: {path}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
