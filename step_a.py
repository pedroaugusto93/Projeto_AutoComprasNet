 # page_start.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helpers import titulo, justificativa, data_inicial, data_final
from selenium.webdriver.common.keys import Keys

import time
import unicodedata


# Pré-cadastro

# Clicar no "Criar" nova contratação
def abrir_popup(driver, timeout: int = 30):
    w = WebDriverWait(driver, timeout)
    btn = w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.br-button.is-primary, .br-button.is-primary")))
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
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
    """, title_input, titulo())
    time.sleep(0.3)  # curto para o campo processar o input

#Categoria
    w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#categoria-contratacao > span"))).click()
    time.sleep(0.3)  # curto para render da lista
    w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#categoria-contratacao_1 > span"))).click()
    time.sleep(0.3)  # curto para o campo processar o input

#Data estimada de início (não ha na planilha)
    dt_inicio = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#data-data-inicio-contratacao")))
    di = data_inicial()

    # extrai dia, mês, ano
    dd, mm, yyyy = (di if isinstance(di, tuple) else tuple(int(x) for x in str(di).replace("-", "/").split("/")[:3]))

    # decide formato pelo idioma do navegador (en → mm/dd/yyyy, default → dd/mm/yyyy)
    lang = (driver.execute_script("return navigator.language || navigator.userLanguage || 'pt-BR';") or "pt-BR").lower()
    use_mmdd = lang.startswith("en")

    # monta valor
    val = f"{mm:02d}/{dd:02d}/{yyyy:04d}" if use_mmdd else f"{dd:02d}/{mm:02d}/{yyyy:04d}"

    # preenche direto
    dt_inicio.click()
    dt_inicio.send_keys(Keys.CONTROL, "a")
    dt_inicio.send_keys(Keys.DELETE)
    dt_inicio.send_keys(val)
    dt_inicio.send_keys(Keys.ENTER)
    dt_inicio.send_keys(Keys.TAB)
    time.sleep(0.3)  # curto para o campo processar o input

#Data estimada de término (não ha na planilha)
    dt_fim = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#data-data-fim-contratacao")))
    df = data_final()
    dd, mm, yyyy = (df if isinstance(df, tuple) else tuple(int(x) for x in str(df).replace("-", "/").split("/")[:3]))
    val_fim = f"{mm:02d}/{dd:02d}/{yyyy:04d}" if use_mmdd else f"{dd:02d}/{mm:02d}/{yyyy:04d}"
    dt_fim.click()
    dt_fim.send_keys(Keys.CONTROL, "a")
    dt_fim.send_keys(Keys.DELETE)
    dt_fim.send_keys(val_fim)
    dt_fim.send_keys(Keys.ENTER)
    dt_fim.send_keys(Keys.TAB)


#Objeto
    campo_desc = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#descricao-contratacao")))
    from helpers import descricao_objeto

    driver.execute_script("""
      const el = arguments[0], val = arguments[1];
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(el, val ?? '');
      el.dispatchEvent(new Event('input',  { bubbles:true }));
      el.dispatchEvent(new Event('change', { bubbles:true }));
      el.dispatchEvent(new Event('blur',   { bubbles:true }));
    """, campo_desc, descricao_objeto())


# Preencher Justificativa (textarea)
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
    """, inserir_jus, justificativa())
    time.sleep(0.3)  # curto para o campo processar o input
    
    # Botão Concluir
    # Clica no botão "Concluir" e aguarda o modal fechar
    botao = w.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "#modal-criacao-contratacao > div.br-modal-footer.justify-content-end.pt-3 > div > button.br-button.is-secondary"
    )))
    botao.click()
    w.until(EC.invisibility_of_element_located(
        (By.CSS_SELECTOR, "#modal-criacao-contratacao")
    ))
    time.sleep(0.5)  # curto para o modal fechar
# Localizar o curso na lista e clicar em "Editar"
WAIT = 20

# Normaliza strings para comparação
def localizar_contratacao(driver):
    """
    Normaliza o título ALVO primeiro e, em seguida, percorre a tabela para localizar
    a linha correspondente (coluna 4) e clicar no botão 'Editar'.
    """
    # 1) Espera a grid estar presente
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table[id$='-table'] tbody tr[id^='contratacao-']")
        )
    )

    # 2) Normaliza o ALVO (antes de qualquer busca)
    from helpers import titulo
    alvo = titulo() or ""
    alvo = unicodedata.normalize("NFD", str(alvo))
    alvo = "".join(c for c in alvo if unicodedata.category(c) != "Mn")
    alvo = alvo.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    alvo = alvo.replace('"', "").replace("'", "")
    alvo = " ".join(alvo.split()).lower().strip()

    # 3) Percorre as linhas e compara com o alvo já normalizado
    for tr in driver.find_elements(By.CSS_SELECTOR, "table[id$='-table'] tbody tr[id^='contratacao-']"):
        td4 = tr.find_element(By.CSS_SELECTOR, "td:nth-child(4)")
        texto = td4.text or td4.get_attribute("innerText") or ""

        # normaliza o texto da célula
        n = unicodedata.normalize("NFD", texto)
        n = "".join(c for c in n if unicodedata.category(c) != "Mn")
        n = n.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
        n = n.replace('"', "").replace("'", "")
        n = " ".join(n.split()).lower().strip()

        if alvo == n or alvo in n or n in alvo:
            tr_id = tr.get_attribute("id") or ""
            btn = tr.find_element(By.CSS_SELECTOR, "button[id^='editar-contratacao-']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            btn.click()
            return {"tr_id": tr_id, "clicked_edit": True}

    raise TimeoutError(f"Título não localizado na coluna 4: {alvo}")

def run(driver, timeout: int = 30):
    # 1) abre e preenche o popup
    abrir_popup(driver, timeout)

    # 2) espera a grid aparecer (a tal pausa)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table[id$='-table'] tbody tr[id^='contratacao-']")
        )
    )

    # 3 executa a localização (ação), NÃO retorna o valor dela
    localizar_contratacao(driver)




# page_dados_basicos.py

