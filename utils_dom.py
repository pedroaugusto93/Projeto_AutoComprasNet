# utils_dom.py
"""
Utilitários de DOM / Selenium.

Funções de baixo nível reutilizadas pelos page modules: waits, clique/digitação
seguros, set de valor via JS (para Angular/PrimeNG), buscas por texto e captura
de evidências. Sem regras de negócio aqui.
"""

from __future__ import annotations

import re
import time
from typing import List, Optional

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from logger import get_logger

log = get_logger(__name__)


# ------------------------------- FORMATAÇÃO ------------------------------- #
def cur4(valor: str) -> str:
    """Formata número para o padrão pt-BR 'X.XXX,0000' (4 casas decimais)."""
    try:
        num = float(str(valor).replace(".", "").replace(",", ".")) if "," in str(valor) \
            else float(str(valor))
        return f"{num:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,0000"


# ------------------------------ WAIT HELPERS ------------------------------ #
def wait_dom_stable(driver, delay: Optional[float] = None) -> None:
    """Pausa curta para o SPA assentar (evita race condition pós-render)."""
    time.sleep(config.DOM_SETTLE if delay is None else delay)


def is_visible(driver, css_selector: str, timeout: int = 5) -> bool:
    """True se o elemento ficar visível dentro do timeout."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return True
    except TimeoutException:
        return False


def wait_text(driver, css_selector: str, expected_text: str, timeout: int = 10) -> None:
    """Espera até o elemento conter o texto esperado."""
    WebDriverWait(driver, timeout).until(
        lambda d: expected_text in d.find_element(By.CSS_SELECTOR, css_selector).text
    )


# -------------------------- CLICK / TYPE WRAPPERS ------------------------- #
def wclick(driver, css_selector: str, timeout: int = 10) -> None:
    """Clique seguro com 1 retry para stale/timeout."""
    wait = WebDriverWait(driver, timeout)
    for tentativa in range(2):
        try:
            el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            el.click()
            return
        except (TimeoutException, StaleElementReferenceException):
            log.debug("Retentando clique em %s (tentativa %d)", css_selector, tentativa + 1)
            time.sleep(0.5)
    raise TimeoutException(f"Elemento não clicável: {css_selector}")


def wtype(driver, css_selector: str, texto: str, clear: bool = True, timeout: int = 10) -> None:
    """Digita texto num input."""
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )
    if clear:
        el.clear()
    el.send_keys(texto)


# ------------------------------ JS SET VALUE ------------------------------ #
def js_set_value(driver, selector: str, value: str, fire: bool = True) -> None:
    """
    Define valor via JS e dispara eventos. Necessário porque Angular/PrimeNG
    ignoram send_keys em campos controlados/mascarados.
    """
    script = """
    const el = document.querySelector(arguments[0]);
    if (!el) return;
    const val = arguments[1];
    const proto = el instanceof HTMLTextAreaElement
        ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    setter.call(el, val);
    if (arguments[2]) {
      el.dispatchEvent(new Event('input',  { bubbles:true }));
      el.dispatchEvent(new Event('change', { bubbles:true }));
      el.dispatchEvent(new Event('blur',   { bubbles:true }));
    }
    """
    driver.execute_script(script, selector, value, fire)
    time.sleep(0.1)


# ------------------------------ BUSCAS / MATCH ---------------------------- #
def find_rows_by_text(driver, table_css: str, cell_css: str, text_contains: str) -> List:
    """Linhas/células de uma tabela que contêm o texto informado."""
    els = driver.find_elements(By.CSS_SELECTOR, cell_css)
    alvo = text_contains.lower()
    return [el for el in els if alvo in el.text.lower()]


def get_last_item_card_id(driver) -> str:
    """ID numérico do último card <p-card id='item-####'>."""
    cards = driver.find_elements(By.CSS_SELECTOR, "p-card[id^='item-']")
    if not cards:
        raise RuntimeError("Nenhum card de item encontrado.")
    match = re.search(r"item-(\d+)", cards[-1].get_attribute("id"))
    if not match:
        raise RuntimeError("ID de card inválido.")
    return match.group(1)


def find_dc_card_by_value_and_apelido(driver, valor_fmt: str, apelido: str, scope_css: str):
    """Localiza card no DC pelo valor e apelido (texto dentro do fieldset)."""
    scope = driver.find_element(By.CSS_SELECTOR, scope_css)
    alvo_apelido = apelido.lower()
    for card in scope.find_elements(By.CSS_SELECTOR, "p-card"):
        texto = card.text.replace("\n", " ")
        if valor_fmt in texto and alvo_apelido in texto.lower():
            return card
    return None


# --------------------------------- OUTROS --------------------------------- #
def shot(driver, filename: str) -> None:
    """Screenshot de evidência salvo em config.SHOTS_DIR."""
    config.garantir_diretorios()
    caminho = config.SHOTS_DIR / filename
    driver.save_screenshot(str(caminho))
    log.debug("Evidência salva: %s", caminho)


def retry_once(fn):
    """Decorator: repete a função 1 vez em caso de Timeout/StaleElement (SPA)."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (TimeoutException, StaleElementReferenceException):
            log.warning("Instabilidade de DOM em %s; tentando novamente.", fn.__name__)
            time.sleep(0.6)
            return fn(*args, **kwargs)
    return wrapper
