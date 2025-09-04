# main.py
from config import get_driver
from selenium.webdriver.support.ui import WebDriverWait

import page_dados_basicos as p_dados
import page_itens as p_itens
import page_responsaveis as p_resp
import page_anexos as p_anx



TARGET_URL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-artefatos-web/execucao"
NOME_CURSO = "Pós-graduação Lato Sensu “Crianças, Adolescentes e Famílias"

def run_step(name, func, *args, **kwargs):
    return func(*args, **kwargs)

def main():
    driver = get_driver()
    driver.switch_to.window(driver.window_handles[0])
    driver.get(TARGET_URL)
    WebDriverWait(driver, 20).until(lambda d: "/comprasnet-artefatos-web/execucao" in d.current_url)

    # >>> Passe o NOME_CURSO aqui <<<
    run_step("Dados Básicos", p_dados.run, driver, NOME_CURSO)
    #run_step("Itens", p_itens.run, driver)
    #run_step("Anexos", p_anx.run, driver)
    #run_step("Responsáveis", p_resp.run, driver)

if __name__ == "__main__":
    main()

