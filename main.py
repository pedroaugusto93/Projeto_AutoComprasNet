# main.py
from helpers import get_driver
from selenium.webdriver.support.ui import WebDriverWait

import step_a as step_a
import step_b as step_b
import step_c as step_c
import step_d as step_d


TARGET_URL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/execucao"


def main():
    driver = get_driver()
    driver.switch_to.window(driver.window_handles[0])
    driver.get(TARGET_URL)

    # Espera a página principal carregar
    WebDriverWait(driver, 20).until(
        lambda d: "/comprasnet-artefatos-web/execucao" in d.current_url
    )

    # Inicia e executa as etapas
    import step_a
    print(">>> step_a carregado de:", getattr(step_a, "__file__", "sem __file__"))
    print(">>> atributos encontrados:", [n for n in dir(step_a) if not n.startswith("_")])

    step_a.run(driver)
    #step_b.run(driver)
    #step_c.run(driver)
    #step_d.run(driver)

    #input("Processo finalizado. Pressione ENTER para encerrar...")


if __name__ == "__main__":
    main()
