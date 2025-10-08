# page_start.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helpers import get_titulo, get_justificativa
import time


# # Pré-cadastro

# Clicar no "Criar" nova contratação
def abrir_popup(driver, timeout: int = 30):
    w = WebDriverWait(driver, timeout)
    print("🖱️ Clicando em 'Criar' contratação...")
    btn = w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.br-button.is-primary, .br-button.is-primary")))
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
    print("✅ Pop-up acionado, aguardando carregar...")
    time.sleep(1)  # tempo curto pro modal abrir


# Registrar o título do curso
    # Título
    title_input = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#titulo-contratacao")))
    driver.execute_script("""
      const el = arguments[0], val = arguments[1];
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(el, val ?? '');
      el.dispatchEvent(new Event('input',  { bubbles:true }));
      el.dispatchEvent(new Event('change', { bubbles:true }));
      el.dispatchEvent(new Event('blur',   { bubbles:true }));
    """, title_input, get_titulo())

    #Categoria

    #Data estimada de início (não ha na planilha)

    #Data estimada de término (não ha na planilha)

    #Objeto

    # Preencher Justificativa (textarea)
    print("🔍 Procurando campo 'Justificativa'...")
    inserir_jus = w.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "#justificativa-contratacao, textarea[name='justificativa']"))
    )
    driver.execute_script("""
      const el = arguments[0], val = arguments[1];
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(el, val ?? '');
      el.dispatchEvent(new Event('input',  { bubbles:true }));
      el.dispatchEvent(new Event('change', { bubbles:true }));
      el.dispatchEvent(new Event('blur',   { bubbles:true }));
    """, inserir_jus, get_justificativa())
    print("✍️ Justificativa inserida.")
    
def run(driver, timeout: int = 30):
    abrir_popup(driver, timeout)    