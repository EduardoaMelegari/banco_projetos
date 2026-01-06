# Guia Rápido de Configuração - Banco de Projetos DWG Firebase

## 📦 Instalação Rápida (5 minutos)

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Criar projeto Firebase

1. Acesse: https://console.firebase.google.com/
2. "Adicionar projeto" → Digite nome → Continuar
3. (Pode desabilitar Analytics) → Criar projeto

### 3. Ativar Storage

1. Menu lateral: **Storage** → **Começar**
2. Modo teste → Próximo
3. Configurar:
   - **Local**: `us-central1` (sem custos financeiros) ✅
   - **Frequência**: Standard
4. Concluído

### 4. Baixar credenciais

1. ⚙️ Configurações do projeto → **Contas de serviço**
2. **Gerar nova chave privada** → Confirmar
3. Renomear arquivo baixado para: `firebase-credentials.json`
4. Mover para esta pasta (`run/`)

### 5. Configurar .env

```bash
cp .env.example .env
```

Edite `.env` e adicione o nome do bucket:

```env
FIREBASE_BUCKET=banco-projetos-dwg.firebasestorage.app
```

> **Onde achar o bucket?** Firebase Console > Storage > topo da página

### 6. Upload inicial dos DWGs

```bash
# Teste primeiro
python sync_inicial.py --dry-run

# Upload real
python sync_inicial.py
```

### 7. Executar aplicação

```bash
python banco_projetos.py
```

**🔐 Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin`
- **IMPORTANTE**: Altere após primeiro acesso!

### 8. Gerenciar usuários

```bash
python manage_users.py
```

Permite:
- Adicionar novos usuários
- Alterar senhas
- Listar usuários
- Testar login

## ✅ Checklist de Configuração

- [ ] Projeto Firebase criado
- [ ] Firebase Storage ativado
- [ ] Arquivo `firebase-credentials.json` na pasta `run/`
- [ ] Arquivo `.env` criado e configurado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Upload inicial feito (`python sync_inicial.py`)
- [ ] Aplicação funcionando (`python banco_projetos.py`)
- [ ] **Senha padrão alterada** (`python manage_users.py`)

## 🔧 Configurações Avançadas

### Alterar local do cache

Edite `.env`:

```env
LOCAL_CACHE_DIR=/caminho/para/cache
```

### Desabilitar sincronização automática

Edite `.env`:

```env
AUTO_SYNC_ON_START=false
SYNC_INTERVAL=0
```

### Usar modo local (sem Firebase)

Edite `app_config.json`:

```json
{
  "usar_firebase": false
}
```

## 🆘 Problemas Comuns

### ❌ Erro: "Could not load credentials"

**Solução:**

```bash
# Verifique se arquivo existe
ls -la firebase-credentials.json

# Deve estar na pasta run/
pwd  # Deve mostrar: .../banco_projetos/run
```

### ❌ Erro: "Storage bucket not found"

**Solução:**

1. Vá para: https://console.firebase.google.com/
2. Seu projeto > Storage
3. Copie o nome do bucket (ex: `projeto.appspot.com`)
4. Cole no `.env`: `FIREBASE_BUCKET=projeto.appspot.com`

### ❌ Erro: "ModuleNotFoundError: No module named 'firebase_admin'"

**Solução:**

```bash
pip install -r requirements.txt
```

### ⚠️ Aplicação abre mas não lista arquivos

**Solução:**

1. Execute primeiro: `python sync_inicial.py`
2. Ou pressione `F5` na aplicação para sincronizar

## 📚 Documentação Completa

Veja o README.md na raiz do projeto para documentação completa.

## 🔗 Links Úteis

- Firebase Console: https://console.firebase.google.com/
- Documentação Storage: https://firebase.google.com/docs/storage
- Python SDK: https://firebase.google.com/docs/admin/setup

---

Dúvidas? Abra uma issue no repositório.
