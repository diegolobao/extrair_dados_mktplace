import os
import time
import re
import csv
import random
from urllib.parse import quote
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
from selenium.webdriver.common.keys import Keys

# Carrega variáveis de ambiente (.env)
load_dotenv()
EMAIL = os.getenv("SHOPEE_EMAIL")
PASSWORD = os.getenv("SHOPEE_PASSWORD")

if not EMAIL or not PASSWORD:
    raise SystemExit("Credenciais não encontradas no .env (SHOPEE_EMAIL/SHOPEE_PASSWORD)")

# Configurações do Chrome/Selenium
chromedriver_path = r"c:\webdrivers\chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Reduce automation fingerprint
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--window-size=1200,800')
chrome_options.add_argument('--lang=pt-BR')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')
service = Service(executable_path=chromedriver_path)

# Prefer undetected-chromedriver when available
if HAS_UC:
    browser = uc.Chrome(options=chrome_options)
else:
    browser = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(browser, 20)


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


def login_shopee(email: str, password: str) -> bool:
    login_url = "https://shopee.com.br/buyer/login?lang=pt-BR"
    print("Abrindo login Shopee…")
    browser.get(login_url)

    # Tenta diretamente, senão tenta iframes
    target_inputs = ['input[name="loginKey"]', 'input[type="text"]', 'input[autocomplete="username"]']
    target_pass = ['input[name="password"]', 'input[type="password"]']

    sel_user = wait_for_any_selectors(target_inputs, timeout=15)
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

def buscar_produto(nome_produto: str):
    # Usa barra de busca da própria Shopee para reduzir anti-bot
    print("Abrindo página inicial da Shopee…")
    browser.get("https://shopee.com.br/")
    wait_if_verify()

    search_selectors = [
        'input[placeholder*="Buscar"]',
        'input[placeholder*="Procure"]',
        'input[type="search"]',
        'input'
    ]
    sel_search = wait_for_any_selectors(search_selectors, timeout=20)
    if not sel_search:
        print("Campo de busca não encontrado.")
        return []

    query_str = nome_produto
    try:
        search_box = browser.find_element(By.CSS_SELECTOR, sel_search)
        time.sleep(random.uniform(0.3, 0.8))
        search_box.clear()
        for ch in query_str:
            search_box.send_keys(ch)
            time.sleep(random.uniform(0.03, 0.12))
        search_box.send_keys(Keys.ENTER)
    except Exception:
        # Fallback: navega por URL
        url = f"https://shopee.com.br/search?keyword={quote(query_str)}&page=0&sortBy=relevancy"
        browser.get(url)

    wait_if_verify()

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
            # Título
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
            # Preço
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
                    if txtp and ('R$' in txtp or re.search(r"\d", txtp)):
                        m = re.search(r"R\$\s*[\d\.,]+", txtp)
                        price = m.group(0) if m else txtp.strip()
                        break
        except Exception:
            pass
        if title:
            resultados.append({'Produto': title, 'Valor': price})

    print(f"Resultados coletados: {len(resultados)}")
    return resultados
        wait.until(EC.url_contains('shopee.com.br'))
        print("Login Shopee efetuado (ou sessão já ativa).")
        return True
    except TimeoutException:
        print(f"Login não confirmado. URL atual: {browser.current_url}")
        # Human-in-the-loop: aguarda até 120s para resolver CAPTCHA/2FA manualmente
        print("Se houver verificação/anti-bot, conclua manualmente na janela aberta.")
        for _ in range(24):
            time.sleep(5)
            if 'buyer/login' not in browser.current_url:
                print("Login confirmado após ação manual.")
                return True
        return False


def buscar_produto(nome_produto: str):
    query = quote(nome_produto)
    url = f"https://shopee.com.br/search?keyword={query}&page=0&sortBy=relevancy"
    print(f"Abrindo busca: {url}")
    browser.get(url)

    # Aguarda itens de resultado
    item_selectors = [
        'div.shopee-search-item-result__item',
        'div[data-sqe="item"]',
        'div[data-index]'  # fallback
    ]
    sel_item = wait_for_any_selectors(item_selectors, timeout=15)
    if not sel_item:
        print("Itens de busca não encontrados.")
        return []

    time.sleep(2)

    items = browser.find_elements(By.CSS_SELECTOR, sel_item)
    resultados = []
    for it in items:
        title = ''
        price = ''
        try:
            # Tentar localizar título
            title_candidates = [
                '[data-sqe="name"]',
                'div[data-sqe="name"]',
                'div',
                'a'
            ]
            for sel in title_candidates:
                el = it.find_elements(By.CSS_SELECTOR, sel)
                if el:
                    txt = el[0].get_attribute('innerText') or el[0].text
                    if txt and len(txt.strip()) > 0:
                        title = txt.strip()
                        break
            # Tentar localizar preço
            price_candidates = [
                '[data-sqe="price"]',
                'div[data-sqe="price"]',
                'div',
                'span'
            ]
            for sel in price_candidates:
                elp = it.find_elements(By.CSS_SELECTOR, sel)
                if elp:
                    txtp = elp[0].get_attribute('innerText') or elp[0].text
                    if txtp and ('R$' in txtp or re.search(r"\d", txtp)):
                        # Extrai primeiro valor com R$
                        m = re.search(r"R\$\s*[\d\.,]+", txtp)
                        price = m.group(0) if m else txtp.strip()
                        break
        except Exception:
            pass
        if title:
            resultados.append({
                'Produto': title,
                'Valor': price
            })

    print(f"Resultados coletados: {len(resultados)}")
    return resultados


def salvar_csv(resultados, path='resultado_busca_shopee.csv'):
    if not resultados:
        print("Nenhum resultado para salvar.")
        return
    campos = ['Produto', 'Valor']
    try:
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            writer.writerows(resultados)
        print(f"Resultados salvos em {path}")
    except PermissionError:
        ts = time.strftime('%Y%m%d_%H%M%S')
        alt = f"resultado_busca_shopee_{ts}.csv"
        with open(alt, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            writer.writerows(resultados)
        print(f"Arquivo em uso. Salvei em {alt}")


if __name__ == '__main__':
    try:
        if not login_shopee(EMAIL, PASSWORD):
            raise SystemExit("Falha no login da Shopee.")
        print("Login confirmado. Aguardando 10 segundos antes da busca…")
        time.sleep(10)
        termo = "caneta depiladora sobrancelha elétrico"
        resultados = buscar_produto(termo)
        salvar_csv(resultados)
    finally:
        try:
            browser.quit()
        except Exception:
            pass
