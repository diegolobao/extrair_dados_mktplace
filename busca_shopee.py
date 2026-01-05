import os
import time
import random
import subprocess
import shutil
from dotenv import load_dotenv
from selenium import webdriver
try:
    import undetected_chromedriver as uc
    HAS_UC = True
except Exception:
    HAS_UC = False
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
try:
    import pyautogui as pag
    HAS_PYAUTO = True
except Exception:
    HAS_PYAUTO = False
try:
    import pyperclip as clipboard
    HAS_CLIPBOARD = True
except Exception:
    HAS_CLIPBOARD = False
try:
    import pygetwindow as gw
    HAS_PYGETWIN = True
except Exception:
    HAS_PYGETWIN = False
try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False

# Carrega variáveis de ambiente (.env)
load_dotenv()
EMAIL = os.getenv("SHOPEE_EMAIL")
PASSWORD = os.getenv("SHOPEE_PASSWORD")
# Configurações anti-bot via .env
USE_PROFILE = os.getenv("SHOPEE_USE_PROFILE", "false").lower() in ("1", "true", "yes")
PROFILE_DIR = os.getenv("SHOPEE_PROFILE_DIR", "").strip()
MAX_VERIFY_WAIT = int(os.getenv("SHOPEE_MAX_VERIFY_WAIT", "180"))
from dotenv import load_dotenv
load_dotenv()
USE_NATIVE_CHROME = os.getenv("SHOPEE_USE_NATIVE_CHROME", "false").lower() in ("1", "true", "yes")
CHROME_PATH = os.getenv("SHOPEE_CHROME_PATH", "").strip()
ATTACH_DEBUGGER = os.getenv("SHOPEE_ATTACH_DEBUGGER", "false").lower() in ("1", "true", "yes")
DEBUG_PORT = os.getenv("SHOPEE_DEBUG_PORT", "9222").strip()
NAV_METHOD = os.getenv("SHOPEE_NAV_METHOD", "pyautogui").strip().lower()  # 'pyautogui' ou 'devtools'

# No modo manual com DevTools, não exigimos credenciais no .env

# Configurações do Chrome/Selenium
chromedriver_path = r"c:\webdrivers\chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Reduz fingerprint de automação
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
try:
    w = random.randint(1100, 1400)
    h = random.randint(700, 900)
    chrome_options.add_argument(f'--window-size={w},{h}')
except Exception:
    chrome_options.add_argument('--window-size=1200,800')
chrome_options.add_argument('--lang=pt-BR')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # oculta "Chrome is being controlled"
chrome_options.add_experimental_option('useAutomationExtension', False)

# Perfil persistente para reutilizar cookies/sessão
if USE_PROFILE:
    if PROFILE_DIR:
        chrome_options.add_argument(f'--user-data-dir={PROFILE_DIR}')
    else:
        local_profile = os.path.join(os.getcwd(), 'chrome-profile')
        os.makedirs(local_profile, exist_ok=True)
        chrome_options.add_argument(f'--user-data-dir={local_profile}')

browser = None
wait = None
if HAS_PYAUTO:
    pag.FAILSAFE = True
    # Pausa global de 3s após cada ação do PyAutoGUI
    pag.PAUSE = 3

def init_browser():
    global browser, wait
    if browser:
        return
    service = Service(executable_path=chromedriver_path)
    if HAS_UC:
        browser = uc.Chrome(options=chrome_options)
    else:
        browser = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(browser, 20)


def attach_to_debugger():
    """Attach to an already-open Chrome started with --remote-debugging-port."""
    global browser, wait
    if browser:
        return True
    opts = Options()
    # Use same baseline options except automation flags
    opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    try:
        browser = webdriver.Chrome(options=opts)
        wait = WebDriverWait(browser, 20)
        print(f"Conectado ao Chrome via DevTools em 127.0.0.1:{DEBUG_PORT}.")
        return True
    except Exception:
        print("Falha ao conectar ao Chrome via DevTools. Verifique se foi iniciado com --remote-debugging-port.")
        return False


def set_stealth():
    """Tenta reduzir fingerprinting básico após anexar."""
    try:
        browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        browser.execute_script("Object.defineProperty(navigator, 'language', {get: () => 'pt-BR'});")
        browser.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']});")
    except Exception:
        pass


def focus_chrome_window():
    """Tenta focar a janela do Chrome/Shopee automaticamente."""
    focused = False
    if HAS_PYGETWIN:
        titles = [
            'Shopee', 'Google Chrome', 'Chrome', 'Chromium'
        ]
        for t in titles:
            try:
                wins = gw.getWindowsWithTitle(t)
                wins = [w for w in wins if w.isVisible]
                if wins:
                    w = wins[0]
                    try:
                        if w.isMinimized:
                            w.restore()
                        w.activate()
                        time.sleep(0.3)
                        focused = True
                        break
                    except Exception:
                        continue
            except Exception:
                continue
    if not focused and HAS_PYAUTO:
        # Fallback: Alt+Tab para a janela anterior
        try:
            pag.hotkey('alt', 'tab')
            time.sleep(0.4)
            focused = True
        except Exception:
            pass
    return focused


def navigate_url_pyautogui(url: str):
    import pyautogui
    # Foca automaticamente a janela do Chrome
    ok_focus = focus_chrome_window()
    if not ok_focus:
        print("Não consegui focar automaticamente a janela do Chrome. Tente trazê-la para frente manualmente.")
    final_url = url
    print(f"Navegando para: {final_url}")
    time.sleep(0.5 + random.uniform(0.2, 0.6))
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(random.uniform(0.1, 0.3))
    if HAS_CLIPBOARD:
        try:
            clipboard.copy(final_url)
            time.sleep(random.uniform(0.2, 0.4))
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(random.uniform(0.2, 0.4))
        except Exception:
            pyautogui.typewrite(final_url, interval=random.uniform(0.02, 0.06))
    else:
        pyautogui.typewrite(final_url, interval=random.uniform(0.02, 0.06))
    time.sleep(random.uniform(0.1, 0.3))
    pyautogui.press('enter')
    # Pequena movimentação para humanizar
    try:
        pyautogui.moveRel(random.randint(-20, 20), random.randint(-10, 10), duration=random.uniform(0.2, 0.4))
        time.sleep(random.uniform(0.4, 0.8))
    except Exception:
        pass


def _sanitize_filename(name: str) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    out = ''.join(c if c not in bad else '_' for c in name)
    out = out.strip()
    if not out:
        out = 'pagina'
    return out


def save_current_page_html_pyautogui(filename: str):
    """Abre o diálogo de salvar e grava o HTML da aba atual em filename.
    filename deve ser um caminho absoluto com .html."""
    import pyautogui
    ok_focus = focus_chrome_window()
    if not ok_focus:
        print("Não consegui focar automaticamente a janela do Chrome. Tentarei mesmo assim.")
    time.sleep(0.5 + random.uniform(0.2, 0.8))
    pyautogui.hotkey('ctrl', 's')
    time.sleep(random.uniform(0.6, 1.2))
    to_paste = filename
    if HAS_CLIPBOARD:
        try:
            clipboard.copy(to_paste)
            time.sleep(random.uniform(0.2, 0.5))
            pyautogui.hotkey('ctrl', 'v')
        except Exception:
            pyautogui.typewrite(to_paste, interval=random.uniform(0.02, 0.06))
    else:
        pyautogui.typewrite(to_paste, interval=random.uniform(0.02, 0.06))
    time.sleep(random.uniform(0.2, 0.5))
    pyautogui.press('enter')
    # Alguns sistemas mostram confirmação (sobrescrever). Tenta confirmar.
    time.sleep(random.uniform(0.6, 1.2))
    try:
        pyautogui.press('enter')
    except Exception:
        pass


def save_current_page_html_via_clipboard(filename: str):
    """Abre o 'view-source' da aba atual, copia todo o HTML para o clipboard e salva em arquivo.
    Mais confiável do que o diálogo de 'Salvar como'. Fecha a aba de 'view-source' ao final."""
    import pyautogui
    try:
        if not HAS_CLIPBOARD:
            print("Clipboard não disponível. Voltando para salvar via diálogo.")
            return save_current_page_html_pyautogui(filename)
        ok_focus = focus_chrome_window()
        if not ok_focus:
            print("Não consegui focar automaticamente a janela do Chrome. Tentarei mesmo assim.")
        # Temporariamente desativa a pausa global para acelerar este fluxo
        original_pause = pag.PAUSE if HAS_PYAUTO else 0
        try:
            if HAS_PYAUTO:
                pag.PAUSE = 0
            # Abre 'Exibir código-fonte da página'
            time.sleep(0.5 + random.uniform(0.4, 0.9))
            pyautogui.hotkey('ctrl', 'u', _pause=False)
            time.sleep(1.2 + random.uniform(0.8, 1.5))
            # Seleciona tudo e copia
            pyautogui.hotkey('ctrl', 'a', _pause=False)
            time.sleep(random.uniform(0.2, 0.4))
            pyautogui.hotkey('ctrl', 'c', _pause=False)
            # Aguarda clipboard preencher
            html = ''
            for _ in range(30):
                try:
                    html = clipboard.paste()
                except Exception:
                    html = ''
                if html:
                    break
                time.sleep(0.2)
        finally:
            if HAS_PYAUTO:
                pag.PAUSE = original_pause
        if not html:
            print("Clipboard vazio ao tentar copiar o HTML. Tentando salvar via diálogo.")
            # Mantém a aba 'view-source' aberta para não fechar o navegador
            return save_current_page_html_pyautogui(filename)
        # Garante diretório
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except Exception:
            pass
        # Escreve arquivo
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML salvo em: {filename}")
    except KeyboardInterrupt:
        print("Operação interrompida durante salvamento via clipboard. Tentando método alternativo…")
        return fetch_current_url_and_save(filename)
    finally:
        # Mantém a aba 'view-source' aberta para garantir que o navegador fique aberto
        pass


def get_current_url_via_clipboard() -> str:
    """Copia a URL atual do Chrome via Ctrl+L e Ctrl+C."""
    import pyautogui
    ok_focus = focus_chrome_window()
    if not ok_focus:
        print("Não consegui focar automaticamente a janela do Chrome para capturar URL.")
    original_pause = pag.PAUSE if HAS_PYAUTO else 0
    try:
        if HAS_PYAUTO:
            pag.PAUSE = 0
        pyautogui.hotkey('ctrl', 'l', _pause=False)
        time.sleep(random.uniform(0.2, 0.4))
        pyautogui.hotkey('ctrl', 'c', _pause=False)
        time.sleep(random.uniform(0.2, 0.4))
        url = ''
        for _ in range(10):
            try:
                url = clipboard.paste()
            except Exception:
                url = ''
            if url:
                break
            time.sleep(0.2)
        return url
    finally:
        if HAS_PYAUTO:
            pag.PAUSE = original_pause


def fetch_current_url_and_save(filename: str):
    """Usa a URL atual (via clipboard) e salva o HTML com requests."""
    if not HAS_REQUESTS:
        print("Biblioteca requests indisponível. Não foi possível salvar via URL.")
        return False
    url = get_current_url_via_clipboard()
    if not url:
        print("Não foi possível obter a URL atual do navegador.")
        return False
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(resp.text)
        print(f"HTML salvo via requests em: {filename}")
        return True
    except Exception:
        print("Falha ao salvar via requests.")
        return False


def wait_for_any_selectors(selectors, timeout=20):
    for sel in selectors:
        try:
            WebDriverWait(browser, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            return sel
        except TimeoutException:
            continue
    return None


def is_verify_page(url: str) -> bool:
    return ('/verify/captcha' in url) or ('/verify/traffic' in url)


def wait_if_verify(max_wait_sec=180):
    if not is_verify_page(browser.current_url):
        return
    print("Shopee apresentou verificação anti-bot. Aguarde/solucione manualmente…")
    waited = 0
    while waited < max_wait_sec and is_verify_page(browser.current_url):
        time.sleep(5)
        waited += 5
    print("Verificação concluída ou tempo esgotado. Prosseguindo…")


def accept_cookies_if_present():
    selectors = [
        'button#onetrust-accept-btn-handler',
        'button.cookie-accept',
        'button[class*="accept"]'
    ]
    for sel in selectors:
        try:
            btns = browser.find_elements(By.CSS_SELECTOR, sel)
            if btns:
                browser.execute_script("arguments[0].click();", btns[0])
                time.sleep(0.5)
                break
        except Exception:
            continue


def humanize_page():
    try:
        actions = ActionChains(browser)
        actions.move_by_offset(random.randint(5, 30), random.randint(5, 20)).perform()
        time.sleep(random.uniform(0.2, 0.6))
        browser.execute_script('window.scrollBy(0, arguments[0])', random.randint(100, 400))
        time.sleep(random.uniform(0.3, 0.7))
        browser.execute_script('window.scrollBy(0, arguments[0])', -random.randint(50, 200))
    except Exception:
        pass


def pyautogui_login(email: str, password: str) -> bool:
    """Usa PyAutoGUI para digitar login e senha e enviar Enter.
    Assume que os campos estão presentes na página atual.
    """
    if not HAS_PYAUTO:
        print("PyAutoGUI não disponível.")
        return False
    try:
        # Foca campo de e-mail via JS para evitar coordenadas frágeis
        email_sel = ['input[name="loginKey"]', 'input[autocomplete="username"]', 'input[type="text"]']
        sel_user = wait_for_any_selectors(email_sel, timeout=10)
        if not sel_user:
            print("Campo de email não identificado.")
            return False
        el_user = browser.find_element(By.CSS_SELECTOR, sel_user)
        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", el_user)
        time.sleep(0.4)
        browser.execute_script("arguments[0].focus();", el_user)
        time.sleep(random.uniform(0.2, 0.5))

        # Digita e-mail com intervalos
        for ch in email:
            pag.typewrite(ch, interval=random.uniform(0.03, 0.12))
        time.sleep(random.uniform(0.2, 0.5))

        # Foca senha (Tab)
        pag.press('tab')
        time.sleep(random.uniform(0.2, 0.4))

        # Digita senha
        for ch in password:
            pag.typewrite(ch, interval=random.uniform(0.03, 0.12))
        time.sleep(random.uniform(0.2, 0.5))

        # Envia Enter para logar
        pag.press('enter')

        # Aguarda navegação pós-login
        for _ in range(40):
            time.sleep(0.5)
            if 'buyer/login' not in browser.current_url:
                print("Login via PyAutoGUI confirmado.")
                return True
        print("PyAutoGUI: login não confirmado no tempo esperado.")
        return False
    except Exception:
        print("PyAutoGUI: falha ao executar login.")
        return False


def login_shopee(email: str, password: str) -> bool:
    init_browser()
    login_url = "https://shopee.com.br"
    # login_url = "https://shopee.com.br/buyer/login?lang=pt-BR"
    print("Abrindo login Shopee…")
    browser.get(login_url)
    try:
        browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    except Exception:
        pass

    # Aguarda campos estarem presentes
    target_inputs = ['input[name="loginKey"]', 'input[type="text"]', 'input[autocomplete="username"]']
    ok = wait_for_any_selectors(target_inputs, timeout=20)
    if not ok:
        print("Página de login não carregou os campos.")
        return False

    # Aceitar cookies e dar pequenos movimentos humanos
    accept_cookies_if_present()
    humanize_page()

    # Faz login via PyAutoGUI
    if pyautogui_login(email, password):
        return True

    # Se não confirmou, aguarda manualmente verificação/captcha
    wait_if_verify(MAX_VERIFY_WAIT)
    if 'buyer/login' not in browser.current_url:
        print("Login confirmado após verificação manual.")
        return True
    print("Falha no login.")
    return False


def _resolve_chrome_path() -> str:
    if CHROME_PATH and os.path.exists(CHROME_PATH):
        return CHROME_PATH
    # Common install locations
    candidates = [
        # r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        # r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        # os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    # Try PATH
    found = shutil.which("chrome") or shutil.which("google-chrome")
    if found:
        return found
    raise FileNotFoundError("Chrome não encontrado. Defina SHOPEE_CHROME_PATH no .env.")


def launch_native_chrome(url: str):
    chrome = _resolve_chrome_path()
    args = [chrome, "--new-window", url]
    if USE_PROFILE:
        profile_arg = PROFILE_DIR if PROFILE_DIR else os.path.join(os.getcwd(), 'chrome-profile')
        os.makedirs(profile_arg, exist_ok=True)
        args.insert(1, f"--user-data-dir={profile_arg}")
    print(f"Abrindo Chrome nativo: {' '.join(args)}")
    subprocess.Popen(args)
    # Aguarda janela abrir
    time.sleep(3)


def human_mouse_jitter():
    if not HAS_PYAUTO:
        return
    try:
        pag.moveRel(random.randint(5, 30), random.randint(5, 20), duration=random.uniform(0.15, 0.4))
        time.sleep(random.uniform(0.2, 0.6))
        # Pequenos scrolls
        pag.scroll(random.randint(-2, 4))
    except Exception:
        pass


def login_shopee_native(email: str, password: str) -> bool:
    url = "https://shopee.com.br/buyer/login?lang=pt-BR"
    launch_native_chrome(url)
    # Aguarda carregamento inicial
    time.sleep(random.uniform(2.0, 4.0))
    human_mouse_jitter()
    # Navega por Tab até campo de e-mail (tentativa)
    if HAS_PYAUTO:
        try:
            # Algumas tentativas de Tab para alcançar o campo de e-mail
            for _ in range(5):
                pag.press('tab')
                time.sleep(random.uniform(0.15, 0.35))
            # Digita e-mail com possíveis pausas e pequenos jitter
            for ch in email:
                pag.typewrite(ch, interval=random.uniform(0.03, 0.12))
                if random.random() < 0.06:
                    time.sleep(random.uniform(0.05, 0.15))
            time.sleep(random.uniform(0.2, 0.5))
            # Próximo campo: senha
            pag.press('tab')
            time.sleep(random.uniform(0.2, 0.4))
            for ch in password:
                pag.typewrite(ch, interval=random.uniform(0.03, 0.12))
                if random.random() < 0.06:
                    time.sleep(random.uniform(0.05, 0.15))
            time.sleep(random.uniform(0.2, 0.5))
            pag.press('enter')
            # Aguarda pós-login (não temos browser.current_url aqui)
            time.sleep(random.uniform(4.0, 7.0))
            print("Login via Chrome nativo + PyAutoGUI finalizado (verifique visualmente).")
            return True
        except Exception:
            print("Falha no login nativo via PyAutoGUI.")
            return False
    else:
        print("PyAutoGUI indisponível para fluxo nativo.")
        return False


# Removido: lógica de busca por produto (manter apenas login por enquanto)


# Removido: salvar CSV (não aplicável enquanto só fazemos login)


def open_login_page_native():
    url = "https://shopee.com.br/buyer/login?lang=pt-BR"
    launch_native_chrome(url)
    print("Chrome nativo aberto na página de login. Digite manualmente.")
    return True


def open_login_page_selenium():
    # If debugger attach is enabled, try it first
    if ATTACH_DEBUGGER:
        ok = attach_to_debugger()
        if not ok:
            print("Attach falhou; inicializando WebDriver padrão.")
            init_browser()
    else:
        init_browser()
    url = "https://shopee.com.br/buyer/login?lang=pt-BR"
    browser.get(url)
    try:
        browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    except Exception:
        pass
    print("Chrome via WebDriver aberto na página de login. Digite manualmente.")
    return True


def buscar_por_url(query: str):
    from urllib.parse import quote
    q = quote((query or '').strip().lower())
    url = f"https://shopee.com.br/search?keyword={q}&page=0&sortBy=relevancy"
    print(f"Abrindo busca: {url}")
    # Atualiza a aba atual com o link de busca
    try:
        browser.execute_script(f"window.location.href='{url}'")
    except Exception:
        browser.get(url)
    # Aguarda itens de resultado
    item_selectors = [
        'div.shopee-search-item-result__item',
        'div[data-sqe="item"]',
        'div[data-index]'
    ]
    sel_item = wait_for_any_selectors(item_selectors, timeout=20)
    if not sel_item:
        print("Itens de busca não encontrados.")
        return []
    # Scroll incremental para carregar mais itens
    for _ in range(5):
        browser.execute_script('window.scrollBy(0, 800)')
        time.sleep(random.uniform(0.4, 0.9))
    items = browser.find_elements(By.CSS_SELECTOR, sel_item)
    resultados = []
    for it in items:
        title = ''
        price = ''
        try:
            title_candidates = [
                '[data-sqe="name"]',
                'div[data-sqe="name"]',
                'a',
                'div'
            ]
            for sel in title_candidates:
                el = it.find_elements(By.CSS_SELECTOR, sel)
                if el:
                    txt = el[0].get_attribute('innerText') or el[0].text
                    if txt and len(txt.strip()) > 0:
                        title = txt.strip()
                        break
            price_candidates = [
                '[data-sqe="price"]',
                'div[data-sqe="price"]',
                'span',
                'div'
            ]
            for sel in price_candidates:
                elp = it.find_elements(By.CSS_SELECTOR, sel)
                if elp:
                    txtp = elp[0].get_attribute('innerText') or elp[0].text
                    if txtp:
                        import re as _re
                        if ('R$' in txtp) or _re.search(r"\d", txtp):
                            m = _re.search(r"R\$\s*[\d\.,]+", txtp)
                            price = m.group(0) if m else txtp.strip()
                            break
        except Exception:
            pass
        if title:
            resultados.append({'Produto': title, 'Valor': price})
    print(f"Resultados coletados: {len(resultados)}")
    return resultados


if __name__ == '__main__':
    print("Abra o Chrome com DevTools, faça login na Shopee e volte ao console.")
    print("Exemplo (PowerShell):")
    print(f"  & \"$Env:ProgramFiles\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port={DEBUG_PORT} --user-data-dir=\"C:\\Temp\\ChromeDebug\"")

    # Pergunta interativa até obter s/n
    resp = ''
    while resp not in ('s', 'n'):
        try:
            resp = input("Login com sucesso? (s/n): ").strip().lower()
        except EOFError:
            time.sleep(2)
    if resp == 's':
        # Pergunta a consulta
        try:
            consulta = input("Digite o termo para busca (ex: caneta depiladora): ").strip()
        except EOFError:
            consulta = "caneta depiladora sobrancelha elétrico"
        if not consulta:
            consulta = "caneta depiladora sobrancelha elétrico"

        from urllib.parse import quote as _quote
        url_busca = f"https://shopee.com.br/search?keyword={_quote(consulta.strip().lower())}&page=0&sortBy=relevancy"

        # Sempre navegar via PyAutoGUI para evitar detecção
        navigate_url_pyautogui(url_busca)
        print("URL atualizada via PyAutoGUI. Verifique os resultados na aba do Chrome.")
        # Aguarda 5s para garantir carregamento da página antes de salvar
        time.sleep(5)

        # Salva HTML da página atual localmente
        base_dir = os.path.join(os.getcwd(), 'pages')
        os.makedirs(base_dir, exist_ok=True)
        stamp = time.strftime('%Y%m%d_%H%M%S')
        fname = _sanitize_filename(consulta.strip().lower())
        full_path = os.path.join(base_dir, f"search_{fname}_{stamp}.html")
        ok_save = False
        try:
            save_current_page_html_via_clipboard(full_path)
            ok_save = True
        except Exception:
            ok_save = False
        if not ok_save:
            fetch_current_url_and_save(full_path)
        print("Navegador permanecerá aberto para inspeção.")
    else:
        print("Ok. Você pode tentar novamente no navegador e responder 's' depois.")
        # Mantém aberto para nova tentativa manual
    # Não encerra automaticamente para permitir validações visuais
