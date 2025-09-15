# page_start.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TEXTO = "MPRJ não é órgão SISG"

def run(driver, timeout: int = 30):
    w = WebDriverWait(driver, timeout)

    # Clicar no "Criar"
    w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.br-button.is-primary"))).click()


    #Titulo do curso

    #Categoria

    #Data estimada de início (não ha na planilha)

    #Data estimada de término (não ha na planilha)

    #Objeto

    # Preencher Justificativa (textarea)
    ta = w.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#justificativa-contratacao, textarea[name='justificativa']")))
    driver.execute_script("""
      const el = arguments[0], val = arguments[1];
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(el, val);
      el.dispatchEvent(new Event('input',  { bubbles:true }));
      el.dispatchEvent(new Event('change', { bubbles:true }));
      el.dispatchEvent(new Event('blur',   { bubbles:true }));
    """, ta, TEXTO)

    return {"ok": True, "via": "textarea"}
