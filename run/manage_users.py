#!/usr/bin/env python3
"""
Script de gerenciamento de usuários para Banco de Projetos DWG

Use este script para gerenciar usuários sem precisar da interface gráfica.
"""

import sys
import getpass
from auth import AuthManager


def main():
    auth = AuthManager()
    
    print("=" * 60)
    print("🔐 GERENCIAMENTO DE USUÁRIOS - Banco de Projetos DWG")
    print("=" * 60)
    
    while True:
        print("\nOpções:")
        print("  1. Listar usuários")
        print("  2. Adicionar usuário")
        print("  3. Alterar senha")
        print("  4. Testar login")
        print("  5. Sair")
        
        escolha = input("\nEscolha uma opção (1-5): ").strip()
        
        if escolha == "1":
            listar_usuarios(auth)
        elif escolha == "2":
            adicionar_usuario(auth)
        elif escolha == "3":
            alterar_senha(auth)
        elif escolha == "4":
            testar_login(auth)
        elif escolha == "5":
            print("\n✓ Até logo!")
            break
        else:
            print("❌ Opção inválida!")


def listar_usuarios(auth):
    """Lista todos os usuários"""
    print("\n" + "=" * 60)
    print("👥 USUÁRIOS CADASTRADOS")
    print("=" * 60)
    
    usuarios = auth.list_users()
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        return
    
    for user in usuarios:
        tipo_badge = "🔑" if user['tipo'] == 'admin' else "👤"
        print(f"{tipo_badge} {user['username']:<15} | {user['nome']:<25} | {user['tipo']}")


def adicionar_usuario(auth):
    """Adiciona novo usuário"""
    print("\n" + "=" * 60)
    print("➕ ADICIONAR NOVO USUÁRIO")
    print("=" * 60)
    
    username = input("Nome de usuário: ").strip()
    if not username:
        print("❌ Nome de usuário não pode ser vazio!")
        return
    
    nome = input("Nome completo: ").strip() or username
    
    print("\nTipo de usuário:")
    print("  1. Admin (pode gerenciar usuários)")
    print("  2. Usuário (apenas acesso)")
    tipo_escolha = input("Escolha (1-2): ").strip()
    tipo = "admin" if tipo_escolha == "1" else "user"
    
    senha = getpass.getpass("Senha: ")
    senha_confirm = getpass.getpass("Confirme a senha: ")
    
    if senha != senha_confirm:
        print("❌ Senhas não conferem!")
        return
    
    if len(senha) < 4:
        print("❌ Senha deve ter pelo menos 4 caracteres!")
        return
    
    if auth.add_user(username, senha, nome, tipo):
        print(f"✓ Usuário '{username}' adicionado com sucesso!")
    else:
        print(f"❌ Usuário '{username}' já existe!")


def alterar_senha(auth):
    """Altera senha de usuário"""
    print("\n" + "=" * 60)
    print("🔑 ALTERAR SENHA")
    print("=" * 60)
    
    username = input("Nome de usuário: ").strip()
    if not username:
        print("❌ Nome de usuário não pode ser vazio!")
        return
    
    senha_atual = getpass.getpass("Senha atual: ")
    senha_nova = getpass.getpass("Nova senha: ")
    senha_confirm = getpass.getpass("Confirme nova senha: ")
    
    if senha_nova != senha_confirm:
        print("❌ Senhas não conferem!")
        return
    
    if len(senha_nova) < 4:
        print("❌ Senha deve ter pelo menos 4 caracteres!")
        return
    
    if auth.change_password(username, senha_atual, senha_nova):
        print(f"✓ Senha de '{username}' alterada com sucesso!")
    else:
        print("❌ Senha atual incorreta!")


def testar_login(auth):
    """Testa credenciais de login"""
    print("\n" + "=" * 60)
    print("🔍 TESTAR LOGIN")
    print("=" * 60)
    
    username = input("Usuário: ").strip()
    senha = getpass.getpass("Senha: ")
    
    if auth.authenticate(username, senha):
        user_info = auth.get_user_info(username)
        print(f"✓ Login bem-sucedido!")
        print(f"  Nome: {user_info['nome']}")
        print(f"  Tipo: {user_info['tipo']}")
    else:
        print("❌ Usuário ou senha incorretos!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Operação cancelada pelo usuário.")
        sys.exit(0)
