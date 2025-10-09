# main.py
from helpers import get_driver
from selenium.webdriver.support.ui import WebDriverWait

import step_a as step_a
import step_b as step_b
import step_c as step_c
import step_d as step_d


TARGET_URL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/execucao"

def open_fresh_tab(driver, url):
    # Garante que existe ao menos uma janela
    if not driver.window_handles:
        raise RuntimeError("Chrome conectado, mas sem janelas abertas.")
    # Se o handle atual estiver inválido, pega o último válido
    try:
        _ = driver.current_url  # força acesso para detectar NoSuchWindow
    except Exception:
        driver.switch_to.window(driver.window_handles[-1])

    # Sempre usa uma aba nova (evita tabs “sistêmicas” ou já controladas)
    driver.execute_script("window.open('about:blank','_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)


def main():
    driver = get_driver()
    driver.switch_to.window(driver.window_handles[0])
    driver.get(TARGET_URL)

    # Espera a página principal carregar
    WebDriverWait(driver, 20).until(
        lambda d: "/comprasnet-artefatos-web/execucao" in d.current_url
    )

    # Inicia e executa as etapas
    step_a.run(driver)
    #step_b.run(driver)
    #step_c.run(driver)
    #step_d.run(driver)

    #input("Processo finalizado. Pressione ENTER para encerrar...")


if __name__ == "__main__":
    main()