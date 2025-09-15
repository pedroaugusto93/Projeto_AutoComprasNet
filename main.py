# main.py
from config import get_driver
from selenium.webdriver.support.ui import WebDriverWait

import page_start as p_start
import getRecord as p_record
import page_dadosBasicos as p_dados
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

    # 1) Start (abre/valida sessão, seleciona unidade, etc.)
    run_step("Start", p_start.run, driver)
   
    # 2) Carrega dados da planilha / prepara registros
    #run_step("Carregar Registros", p_record.run, driver)

    # 3) Dados Básicos (usa o NOME_CURSO abaixo)
    #run_step("Dados Básicos", p_dados.run, driver, NOME_CURSO)
    
    # 4) Itens
    # run_step("Itens", p_itens.run, driver)

    # 5) Anexos
    # run_step("Anexos", p_anx.run, driver)

    # 6) Responsáveis
    # run_step("Responsáveis", p_resp.run, driver)

if __name__ == "__main__":
    main()

