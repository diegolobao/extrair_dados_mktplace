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

## Abrir o Chrome (Windows)
Para o fluxo atual (navegação com PyAutoGUI), a forma mais estável é abrir o Chrome normalmente, fazer login manual na Shopee e deixar a aba aberta. Caso você queira anexar a uma sessão com DevTools para depuração, use a opção com porta de depuração.

### Opção 1 — Chrome normal (recomendado)
- Abra o Chrome como de costume e faça login manual na Shopee.
- Mantenha a janela/aba visível; o script tenta focar a janela automaticamente antes de navegar.

### Opção 2 — Chrome com DevTools (anexo opcional)
No PowerShell, execute:

```powershell
& "$Env:ProgramFiles\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Temp\ChromeDebug"
```

- `--remote-debugging-port=9222`: habilita o DevTools para anexar a uma sessão já aberta.
- `--user-data-dir`: use um diretório dedicado (como `C:\Temp\ChromeDebug`) para evitar travar seu perfil principal.
- Depois, faça login na Shopee nessa janela.

### Dicas de foco da janela
- Se o foco automático falhar (políticas de janela/antivírus), traga o Chrome para frente manualmente (Alt+Tab) e tente novamente.
- Evite minimizar o Chrome durante o fluxo — manter visível ajuda o PyAutoGUI a enviar as teclas corretamente.

### Observações do fluxo
- O script atual atualiza a URL da aba com PyAutoGUI (`Ctrl+L`, colar link, `Enter`) e aguarda 5s antes de salvar o HTML.
- O HTML é salvo em `pages/search_<termo>_<timestamp>.html` e a janela do navegador permanece aberta.
