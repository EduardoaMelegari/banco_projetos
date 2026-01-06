# 🔨 Guia de Compilação - Executável Windows (.exe)

Este guia explica como compilar a aplicação Python em um executável Windows portátil.

## 📦 Requisitos

- Python 3.8 ou superior
- Windows (para gerar .exe)
- Todas as dependências instaladas

## 🚀 Passo a Passo

### 1. Instalar PyInstaller

```bash
cd run
pip install pyinstaller
# ou
pip install -r requirements.txt
```

### 2. Executar o script de build

```bash
python build_exe.py
```

O script irá:
- ✅ Limpar builds anteriores
- 🔨 Compilar a aplicação com PyInstaller
- 📦 Criar pasta `BancoProjetosDWG_Portable/`
- 📄 Gerar arquivos de configuração e documentação

### 3. Resultado

Será criada a pasta `BancoProjetosDWG_Portable/` contendo:

```
BancoProjetosDWG_Portable/
├── BancoProjetosDWG.exe     # Executável principal (~30-50 MB)
├── .env.example             # Modelo de configuração
└── LEIA-ME.txt              # Instruções de uso
```

### 4. Preparar para distribuição

**Adicione os arquivos necessários:**

```bash
# Copie suas credenciais Firebase
copy firebase-credentials.json BancoProjetosDWG_Portable/

# Copie e configure o .env
copy .env.example BancoProjetosDWG_Portable/.env
# Edite o .env com suas configurações
```

### 5. Distribuir

**Comprima a pasta em ZIP:**

```bash
# Windows Explorer: Botão direito > Enviar para > Pasta compactada
# Ou use 7-Zip, WinRAR, etc.
```

**Resultado final:** `BancoProjetosDWG_Portable.zip` (~30-50 MB)

## ⚙️ Opções Avançadas

### Compilar manualmente com PyInstaller

```bash
pyinstaller --name=BancoProjetosDWG ^
            --onefile ^
            --windowed ^
            --add-data=firebase_sync.py;. ^
            --add-data=auth.py;. ^
            --hidden-import=firebase_admin ^
            --noconfirm ^
            banco_projetos.py
```

### Opções úteis

| Opção | Descrição |
|-------|-----------|
| `--onefile` | Gera um único .exe |
| `--onedir` | Gera pasta com .exe + DLLs (mais rápido) |
| `--windowed` | Sem console (apenas GUI) |
| `--console` | Com console (útil para debug) |
| `--icon=icon.ico` | Adiciona ícone personalizado |
| `--name=Nome` | Nome do executável |

### Adicionar ícone

1. Crie ou baixe um arquivo `.ico`
2. Salve como `icon.ico` na pasta `run/`
3. No `build_exe.py`, altere:
   ```python
   '--icon=icon.ico',
   ```

## 🐛 Solução de Problemas

### ❌ "PyInstaller not found"

```bash
pip install pyinstaller
```

### ❌ Executável muito grande

Use `--onedir` em vez de `--onefile`:
- Gera pasta com múltiplos arquivos
- Executável menor (~5 MB)
- Inicialização mais rápida

### ❌ Antivírus bloqueia o .exe

- Normal para executáveis gerados por PyInstaller
- Adicione exceção no antivírus
- Ou assine digitalmente o executável

### ❌ Erro ao executar o .exe

Execute pelo CMD para ver erros:
```bash
cd BancoProjetosDWG_Portable
BancoProjetosDWG.exe
```

### ❌ Módulo não encontrado

Adicione ao `build_exe.py`:
```python
'--hidden-import=nome_do_modulo',
```

## 📊 Comparação de Modos

| Modo | Tamanho | Velocidade | Arquivos |
|------|---------|------------|----------|
| `--onefile` | ~40 MB | Mais lento | 1 arquivo |
| `--onedir` | ~80 MB | Mais rápido | Pasta com vários |

**Recomendação:** `--onefile` para distribuição fácil.

## ✅ Checklist de Distribuição

Antes de distribuir o executável:

- [ ] Testou o .exe em máquina limpa (sem Python)
- [ ] Incluiu `firebase-credentials.json`
- [ ] Configurou `.env` corretamente
- [ ] Incluiu `LEIA-ME.txt` com instruções
- [ ] Testou login com admin/admin
- [ ] Testou sincronização Firebase
- [ ] Testou busca e cópia de arquivos
- [ ] Criou ZIP para distribuição

## 📦 Distribuição

### Opção 1: ZIP Manual

```
BancoProjetosDWG_v1.0.zip
└── BancoProjetosDWG_Portable/
    ├── BancoProjetosDWG.exe
    ├── firebase-credentials.json
    ├── .env
    └── LEIA-ME.txt
```

### Opção 2: Instalador (opcional)

Use ferramentas como:
- **Inno Setup** (gratuito)
- **NSIS** (gratuito)
- **Advanced Installer** (pago)

## 🔄 Atualização de Versão

Para atualizar o executável:

1. Faça alterações no código Python
2. Execute `python build_exe.py` novamente
3. Distribua novo ZIP

## 💡 Dicas

- **Tamanho:** O .exe inclui Python + bibliotecas (~40 MB)
- **Portabilidade:** Funciona em qualquer Windows sem instalar Python
- **Performance:** Mesma performance da versão Python
- **Segurança:** Credenciais ficam na pasta do usuário

## 📞 Suporte

- **Documentação PyInstaller:** https://pyinstaller.org/
- **Issues:** https://github.com/EduardoaMelegari/banco_projetos/issues

---

**Última atualização:** Janeiro 2026
