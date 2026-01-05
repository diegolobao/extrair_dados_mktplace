# Guia do ambiente virtual `env`

Este documento explica como ativar (acessar) e desativar o ambiente virtual `env` neste projeto.

## Pré-requisitos
- Windows (PowerShell ou Prompt de Comando)
- Estar na pasta do projeto: `C:\Users\lobao\Desktop\Projetos VS Code\Extrair Shopee`

## Ativar o ambiente (PowerShell)
No PowerShell, execute:

```powershell
# Dentro da pasta do projeto
.\env\Scripts\Activate.ps1
```

Se aparecer erro de política de execução, habilite scripts do usuário e tente novamente:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\env\Scripts\Activate.ps1
```

## Ativar o ambiente (Prompt de Comando - cmd)
No Prompt de Comando, execute:

```cmd
.\env\Scripts\activate.bat
```

## Desativar o ambiente
Em qualquer shell (PowerShell ou cmd), execute:

```powershell
deactivate
```

## Selecionar o intérprete no VS Code
- Abra a Command Palette: `Ctrl+Shift+P`
- Busque por: `Python: Select Interpreter`
- Selecione o Python dentro de `env` (caminho termina em `env\Scripts\python.exe`).

## Dicas
- Para instalar dependências: `pip install -r requirements.txt` (se existir o arquivo).
- Para conferir o Python ativo: `python --version`.
