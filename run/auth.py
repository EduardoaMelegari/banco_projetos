"""
Módulo de autenticação para o Banco de Projetos DWG

Gerencia login e senha de usuários com segurança
"""

import json
import hashlib
import os
from typing import Optional, Dict


class AuthManager:
    """Gerenciador de autenticação de usuários"""
    
    def __init__(self, users_file: str = "users.json"):
        """
        Inicializa gerenciador de autenticação
        
        Args:
            users_file: Caminho do arquivo de usuários
        """
        self.users_file = users_file
        self.users_data = self._load_users()
        
        # Criar usuário padrão se não existir nenhum
        if not self.users_data:
            self._create_default_user()
    
    def _load_users(self) -> Dict:
        """Carrega dados de usuários do arquivo"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_users(self):
        """Salva dados de usuários no arquivo"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar usuários: {e}")
    
    def _hash_password(self, password: str) -> str:
        """
        Cria hash SHA-256 da senha
        
        Args:
            password: Senha em texto plano
            
        Returns:
            Hash da senha
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _create_default_user(self):
        """Cria usuário padrão admin/admin"""
        self.users_data = {
            "users": {
                "admin": {
                    "password_hash": self._hash_password("admin"),
                    "nome": "Administrador",
                    "tipo": "admin"
                }
            }
        }
        self._save_users()
        print("⚠️ Usuário padrão criado: admin/admin")
        print("   IMPORTANTE: Altere a senha após o primeiro login!")
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Autentica usuário
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            True se autenticado, False caso contrário
        """
        if not username or not password:
            return False
        
        users = self.users_data.get("users", {})
        if username not in users:
            return False
        
        password_hash = self._hash_password(password)
        return users[username]["password_hash"] == password_hash
    
    def add_user(self, username: str, password: str, nome: str = "", tipo: str = "user") -> bool:
        """
        Adiciona novo usuário
        
        Args:
            username: Nome de usuário
            password: Senha
            nome: Nome completo
            tipo: Tipo de usuário (admin/user)
            
        Returns:
            True se adicionado, False se já existe
        """
        users = self.users_data.get("users", {})
        
        if username in users:
            return False
        
        users[username] = {
            "password_hash": self._hash_password(password),
            "nome": nome or username,
            "tipo": tipo
        }
        
        self.users_data["users"] = users
        self._save_users()
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Altera senha de usuário
        
        Args:
            username: Nome de usuário
            old_password: Senha atual
            new_password: Nova senha
            
        Returns:
            True se alterado, False se senha atual incorreta
        """
        if not self.authenticate(username, old_password):
            return False
        
        users = self.users_data.get("users", {})
        users[username]["password_hash"] = self._hash_password(new_password)
        self._save_users()
        return True
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Retorna informações do usuário (sem senha)
        
        Args:
            username: Nome de usuário
            
        Returns:
            Dicionário com info do usuário ou None
        """
        users = self.users_data.get("users", {})
        if username in users:
            user = users[username].copy()
            user.pop("password_hash", None)
            return user
        return None
    
    def list_users(self) -> list:
        """Lista todos os usuários (sem senhas)"""
        users = self.users_data.get("users", {})
        result = []
        for username, data in users.items():
            result.append({
                "username": username,
                "nome": data.get("nome", username),
                "tipo": data.get("tipo", "user")
            })
        return result


if __name__ == "__main__":
    # Teste do módulo
    print("🔐 Teste do módulo de autenticação\n")
    
    auth = AuthManager("test_users.json")
    
    # Testar autenticação
    print("Testando login admin/admin:")
    if auth.authenticate("admin", "admin"):
        print("✓ Login bem-sucedido!")
    else:
        print("✗ Login falhou")
    
    # Adicionar usuário
    print("\nAdicionando usuário 'usuario':")
    if auth.add_user("usuario", "senha123", "Usuário Teste"):
        print("✓ Usuário adicionado")
    else:
        print("✗ Usuário já existe")
    
    # Listar usuários
    print("\nUsuários cadastrados:")
    for user in auth.list_users():
        print(f"  • {user['username']} - {user['nome']} ({user['tipo']})")
    
    # Limpar arquivo de teste
    if os.path.exists("test_users.json"):
        os.remove("test_users.json")
        print("\n✓ Arquivo de teste removido")
