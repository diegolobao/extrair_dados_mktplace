import os
import re
import time
import pandas as pd
from getpass import getpass
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# NÃO usar perfil do Chrome para teste
chrome_options = Options()


# Caminho do chromedriver.exe (ajuste se necessário)
chromedriver_path = r"c:\webdrivers\chromedriver.exe"  # Corrigido para raw string
service = Service(executable_path=chromedriver_path)

# Flags para evitar crash do Chrome ao usar perfil
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Inicializa o navegador com o perfil logado
browser = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(browser, 20)

def find_first(selector_list):
    for sel in selector_list:
        els = browser.find_elements(By.CSS_SELECTOR, sel)
        if els:
            return els[0]
    return None

def login(email: str, password: str) -> bool:
    login_url = "https://app.seuarmazemdrop.com.br/login"
    print("Abrindo página de login…")
    browser.get(login_url)
    try:
        # Espera elementos do formulário
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="email"]')))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"], input[name="password"]')))
    except TimeoutException:
        print("Formulário de login não carregou.")
        return False

    email_input = find_first(['input[name="email"]', 'input[type="email"]', '#email'])
    password_input = find_first(['input[name="password"]', 'input[type="password"]', '#password'])
    submit_btn = None
    # Tenta localizar botão de envio
    submit_btn = find_first(['button[type="submit"]', 'button.btn-primary', 'button'])

    if not email_input or not password_input:
        print("Campos de email/senha não encontrados.")
        return False

    email_input.clear(); email_input.send_keys(email)
    password_input.clear(); password_input.send_keys(password)

    if submit_btn:
        submit_btn.click()
    else:
        # Fallback: envia Enter no campo de senha
        password_input.submit()

    try:
        # Aguarda redirecionar para dashboard
        wait.until(EC.url_contains('/dashboard'))
        print("Login efetuado com sucesso.")
        return True
    except TimeoutException:
        print(f"Login não confirmado. URL atual: {browser.current_url}")
        return False

# Parâmetros
base_url = "https://app.seuarmazemdrop.com.br/dashboard/catalog?per_page=100&page="
# Processar todas as 14 páginas
num_pages = 14

produtos = []

# Credenciais: usa variáveis de ambiente, senão pergunta no console
email = os.environ.get("SEUARMAZEM_EMAIL")
password = os.environ.get("SEUARMAZEM_PASSWORD")
if not email:
    email = input("Email de login: ")
if not password:
    password = getpass("Senha: ")

if not login(email, password):
    print("Falha no login. Encerrando.")
    browser.quit()
    raise SystemExit(1)

print("Iniciando extração…")
print("Processando 14 páginas do catálogo…")

def wait_for_any_selectors(selectors, timeout=20):
    """Wait until any one of the provided CSS selectors is present."""
    for sel in selectors:
        try:
            WebDriverWait(browser, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            return sel
        except TimeoutException:
            continue
    return None

def ensure_page_ready():
    """Ensure catalog elements are present; switch into iframe if needed."""
    target_selectors = ['a.text-dark', 'div.product-price-tag', 'span.text-muted']
    # Try direct presence
    if wait_for_any_selectors(target_selectors, timeout=10):
        return True

    # Check iframes
    frames = browser.find_elements(By.TAG_NAME, 'iframe')
    print(f"Iframes encontrados: {len(frames)}")
    for idx, frame in enumerate(frames):
        try:
            browser.switch_to.frame(frame)
            print(f"Alternando para iframe #{idx}")
            if wait_for_any_selectors(target_selectors, timeout=10):
                return True
        except Exception:
            # Volta ao contexto padrão e tenta próximo frame
            browser.switch_to.default_content()
            continue
    # Volta ao contexto padrão
    browser.switch_to.default_content()
    return False

def scroll_to_load_all(max_steps=25, pause=0.7):
    """Scrolls the page and any scrollable containers to trigger lazy loading."""
    last_height = browser.execute_script('return document.body.scrollHeight')
    for step in range(max_steps):
        # Scroll viewport to bottom
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(pause)
        new_height = browser.execute_script('return document.body.scrollHeight')

        # Try scrolling internal scrollable containers
        try:
            scrolled = browser.execute_script(
                """
                var scrolledAny = false;
                var els = document.querySelectorAll('div,section,main,tbody');
                els.forEach(function(el){
                    var style = getComputedStyle(el);
                    if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight){
                        el.scrollTop = el.scrollHeight;
                        scrolledAny = true;
                    }
                });
                return scrolledAny;
                """
            )
        except Exception:
            scrolled = False

        # Break if neither viewport nor containers increased height
        if new_height == last_height and not scrolled:
            break
        last_height = new_height

    # Small pause to allow final render
    time.sleep(pause)

def parse_page(html: str):
    soup = BeautifulSoup(html, 'lxml')
    items = []

    # Ponto de partida: todos os nomes de produto
    name_links = soup.select('a.text-dark')

    def find_container(el):
        # Sobe alguns níveis para achar um container contendo preço/atributos
        parent = el.parent
        for _ in range(8):
            if not parent or not getattr(parent, 'parent', None):
                break
            if parent.select_one('div.product-price-tag') or parent.select_one('span.text-muted'):
                return parent
            parent = parent.parent
        return el.parent

    for link in name_links:
        nome_full = link.get_text(strip=True)
        sku = ''
        nome = nome_full
        m = re.match(r"^\(([^)]+)\)\s*(.+)$", nome_full)
        if m:
            sku = m.group(1).strip()
            nome = m.group(2).strip()
        container = find_container(link)

        # Valor (preço)
        valor_el = container.select_one('div.product-price-tag')
        valor = valor_el.get_text(strip=True) if valor_el else ''

        # Atributos: Cor, Tamanho, Estoque
        cor = ''
        tamanho = ''
        estoque = ''
        for sp in container.select('span.text-muted'):
            txt = sp.get_text(strip=True)
            if txt.lower().startswith('cor') and ':' in txt:
                cor = txt.split(':', 1)[1].strip()
            elif txt.lower().startswith('tamanho') and ':' in txt:
                tamanho = txt.split(':', 1)[1].strip()
            elif txt.lower().startswith('estoque') and ':' in txt:
                est_val = txt.split(':', 1)[1].strip()
                # remove sufixos como "pcs"
                estoque = re.sub(r'[^0-9]', '', est_val)

        items.append({
            'SKU': sku,
            'Produto': nome,
            'Valor': valor,
            'Cor': cor,
            'Tamanho': tamanho,
            'Estoque': estoque,
        })

    return items

## Removed duplicate parse_page definition; using the version above that starts from a.text-dark


for page in range(1, num_pages + 1):
    url = f"{base_url}{page}"
    print(f"Acessando: {url}")
    browser.get(url)
    # Aguarda elementos e tenta lidar com iframe
    ready = ensure_page_ready()
    if not ready:
        # Faz scroll para disparar lazy-loading e tenta novamente
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        sel = wait_for_any_selectors(['a.text-dark','div.product-price-tag','span.text-muted'], timeout=10)
        if not sel:
            print("Elementos do catálogo não encontrados após espera.")

    # Ensure all items are rendered by scrolling
    scroll_to_load_all()
    print(f"Página carregada: {browser.current_url}")

    # Depuração: salvar screenshot para ver se está logado
    browser.save_screenshot(f"screenshot_pagina_{page}.png")
    # Dump de HTML para análise (após scroll)
    try:
        html_dump = browser.page_source
        with open(f"pagina_{page}.html", 'w', encoding='utf-8') as f:
            f.write(html_dump)
    except Exception:
        pass

    # Parse da página com BeautifulSoup
    html = browser.page_source
    items = parse_page(html)
    print(f"Itens extraídos nesta página: {len(items)}")
    if len(items) == 0:
        try:
            # Debug: quantos nomes foram encontrados diretamente
            soup_dbg = BeautifulSoup(html, 'lxml')
            dbg_names = soup_dbg.select('a.text-dark')
            print(f"[Depuração] a.text-dark encontrados no HTML: {len(dbg_names)}")
        except Exception:
            pass
    produtos.extend(items)

browser.quit()

# Salva em CSV (ordem de colunas estável) com delimitador ';' e fallback se arquivo estiver em uso
df = pd.DataFrame(produtos, columns=["SKU", "Produto", "Valor", "Cor", "Tamanho", "Estoque"])
output_path = "produtos_catalogo.csv"
try:
    df.to_csv(output_path, index=False, encoding="utf-8-sig", sep=';')
    print(f"Extração finalizada. {len(produtos)} produtos salvos em {output_path}")
except PermissionError:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    alt_path = f"produtos_catalogo_{ts}.csv"
    df.to_csv(alt_path, index=False, encoding="utf-8-sig", sep=';')
    print(f"Aviso: {output_path} está em uso. Salvei {len(produtos)} produtos em {alt_path}.")
