# page_start.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helpers import load_data, get_nome_curso, get_objeto

def run(driver, timeout: int = 30):
    wait = WebDriverWait(driver, timeout)
    botao = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.br-button.is-primary")))

    botao.click()

