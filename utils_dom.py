# utils_dom.py
"""
Funções utilitárias de manipulação de DOM / Selenium
Usadas em vários steps do ComprasNet (bypass máscara, waits, etc.)
"""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


# -------- FORMATAÇÃO --------
def cur4(valor: str) -> str:
    """Formata número (str) para padrão 'X,0000' com 4 casas decimais."""
    try:
        num = float(str(valor).replace(",", "."))
        return f"{num:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,0000"


# -------- WAIT HELPERS --------
def wait_dom_stable(driver, delay: float = 0.5):
    """Aguarda pequenas mudanças no DOM para evitar race condition."""
    time.sleep(delay)


def is_visible(driver, css_selector: str, timeout: int = 5) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return True
    except TimeoutException:
        return False


# -------- CLICK / TYPE WRAPPERS --------
def wclick(driver, css_selector: str, timeout: int = 10):
    """Click seguro com retry em caso de stale/timeout."""
    w = WebDriverWait(driver, timeout)
    for _ in range(2):
        try:
            el = w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            el.click()
            return
        except (TimeoutException, StaleElementReferenceException):
            time.sleep(0.5)
    raise TimeoutException(f"Elemento não clicável: {css_selector}")


def wtype(driver, css_selector: str, texto: str, clear: bool = True, timeout: int = 10):
    """Digita texto num input."""
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )
    if clear:
        el.clear()
    el.send_keys(texto)


# -------- JS SET VALUE --------
def js_set_value(driver, selector: str, value: str, fire: bool = True):
    """Define valor via JS e dispara eventos (para Angular/PrimeNG)."""
    script = """
    const el = document.querySelector(arguments[0]);
    if (!el) return;
    const val = arguments[1];
    const setter = Object.getOwnPropertyDescriptor(el.__proto__, 'value').set;
    setter.call(el, val);
    if (arguments[2]) {
      el.dispatchEvent(new Event('input',  { bubbles:true }));
      el.dispatchEvent(new Event('change', { bubbles:true }));
      el.dispatchEvent(new Event('blur',   { bubbles:true }));
    }
    """
    driver.execute_script(script, selector, value, fire)
    time.sleep(0.1)


# -------- BUSCAS / MATCH --------
def find_rows_by_text(driver, table_css: str, cell_css: str, text_contains: str):
    """Procura linhas em uma tabela que contenham o texto informado."""
    els = driver.find_elements(By.CSS_SELECTOR, cell_css)
    return [el for el in els if text_contains.lower() in el.text.lower()]


def get_last_item_card_id(driver) -> str:
    """Pega o ID numérico do último card <p-card id='item-####'>."""
    cards = driver.find_elements(By.CSS_SELECTOR, "p-card[id^='item-']")
    if not cards:
        raise RuntimeError("Nenhum card de item encontrado.")
    last = cards[-1]
    match = re.search(r"item-(\d+)", last.get_attribute("id"))
    if not match:
        raise RuntimeError("ID de card inválido.")
    return match.group(1)


def find_dc_card_by_value_and_apelido(driver, valor_fmt: str, apelido: str, scope_css: str):
    """Localiza card no DC pelo valor e apelido (texto em spans dentro do fieldset)."""
    scope = driver.find_element(By.CSS_SELECTOR, scope_css)
    cards = scope.find_elements(By.CSS_SELECTOR, "p-card")
    for c in cards:
        texto = c.text.replace("\n", " ")
        if (valor_fmt in texto) and (apelido.lower() in texto.lower()):
            return c
    return None


# -------- OUTROS --------
def wait_text(driver, css_selector: str, expected_text: str, timeout: int = 10):
    """Espera até que o elemento contenha o texto esperado."""
    w = WebDriverWait(driver, timeout)
    w.until(lambda d: expected_text in d.find_element(By.CSS_SELECTOR, css_selector).text)


def shot(driver, filename: str):
    """Screenshot simples para logs/evidências."""
    driver.save_screenshot(f"logs/{filename}")

# --- RETRY DECORATOR (1 tentativa extra) ---
def retry_once(fn):
    """
    Executa a função e, se falhar com Timeout/StaleElement, tenta mais 1 vez.
    Útil para instabilidades de DOM em SPAs (PrimeNG/Angular).
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (TimeoutException, StaleElementReferenceException) as e:
            time.sleep(0.6)
            return fn(*args, **kwargs)
    return wrapper

import os  # <- já deve estar no topo (se não estiver, importe)

def shot(driver, filename: str):
    """Screenshot simples para logs/evidências."""
    os.makedirs("logs", exist_ok=True)
    driver.save_screenshot(os.path.join("logs", filename))
