# main.py
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

import step_a
import step_b

# ---- Config ----
TARGET_URL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/execucao"
CHROME_DEBUG_HOST = os.getenv("CHROME_DEBUG_HOST", "127.0.0.1")
CHROME_DEBUG_PORT = os.getenv("CHROME_DEBUG_PORT", "9222")
DEFAULT_TIMEOUT = int(os.getenv("TIMEOUT_SECONDS", "20"))

def get_driver():
    """
    Conecta no Chrome já aberto em modo Remote Debugging.
    Abra o Chrome antes com, por exemplo (Windows):
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
        --remote-debugging-port=9222 ^
        --user-data-dir="C:\\chrome_debug"
    """
    chrome_options = Options()
    chrome_options.debugger_address = f"{CHROME_DEBUG_HOST}:{CHROME_DEBUG_PORT}"
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        raise RuntimeError(
            "Falha ao conectar no Chrome via Remote Debugging. "
            "Confira se o Chrome está aberto com --remote-debugging-port "
            f"({CHROME_DEBUG_HOST}:{CHROME_DEBUG_PORT})."
        ) from e
    driver.set_page_load_timeout(DEFAULT_TIMEOUT)
    return driver

def main():
    driver = get_driver()
    driver.switch_to.window(driver.window_handles[0])
    driver.get(TARGET_URL)

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        lambda d: "/comprasnet-artefatos-web/execucao" in d.current_url
    )

    # Step A (ok no seu ambiente)
    step_a.run(driver)

    # Step B (wrapper run dentro do step_b carrega a planilha e executa o fluxo completo)
    step_b.run(driver)

    print("Fluxo completo finalizado ✅")

if __name__ == "__main__":
    main()
