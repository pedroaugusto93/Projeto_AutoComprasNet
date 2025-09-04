# config.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DEBUG_PORT = 9222  # mesma porta usada ao abrir o Chrome

def get_driver():
    """Conecta ao Chrome já aberto em modo depurador."""
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


