# page_dados_basicos.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WAIT = 20

def run(driver, NOME_CURSO: str):
    wait = WebDriverWait(driver, WAIT)
    
    # 1 - clica na aba "Dados Básicos"
    # espera a tabela renderizar
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#pn_id_13-table tbody")))

    # 2 - localiza a linha (tr) e a célula (td) que contém o NOME_CURSO
    # procura a célula que contém o texto (não depende do td[4])
    td_xpath = f"//table[@id='pn_id_13-table']//td[normalize-space(.)='{NOME_CURSO}']"
    td = wait.until(EC.presence_of_element_located((By.XPATH, td_xpath)))
    
    # 3 - destaca a célula e pega o id da linha
    # rola até a célula
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", td)
    # aplica um destaque visual para "selecionar"
    driver.execute_script("arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';", td)

    # 4 - pega o id da linha (tr)
    # agora sobe até a <tr> pai e pega o atributo id (ex.: contratacao-267555)
    tr = td.find_element(By.XPATH, "./ancestor::tr")
    tr_id = tr.get_attribute("id")

    print(f"[INFO] NOME_CURSO localizado na linha: {tr_id}")

    # 5) Dentro da mesma linha, acha o botão Editar e clica
    #    (primeiro tenta localizar dentro do próprio <tr>)
    try:
        btn = tr.find_element(By.CSS_SELECTOR, "button[id^='editar-contratacao-']")
    except Exception:
        # fallback por id derivado do tr_id
        numero = tr_id.split("-")[-1]
        btn = driver.find_element(By.ID, f"editar-contratacao-{numero}")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    driver.execute_script("arguments[0].click();", btn)
    
    # retorna a linha e a célula para usos posteriores
    return {"tr_id": tr_id, "clicked_edit": True}