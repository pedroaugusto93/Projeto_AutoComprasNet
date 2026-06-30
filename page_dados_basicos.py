# page_dados_basicos.py
"""
Aba "Dados Básicos" (antigo step_a + getRecord).

Fluxo:
  1. criar_contratacao(item)      -> abre o modal e preenche o pré-cadastro.
  2. localizar_contratacao(item)  -> acha a contratação na grid e clica em Editar.
  3. preencher_dados_basicos(item)-> nº do processo e modalidade.

Fontes de dado:
  • Variáveis (vêm da planilha, via ItemContratacao): título (NOME_CURSO),
    objeto (OBJETO), processo (PROCESSO).
  • Constantes (config.Constantes): justificativa, modalidade, fundamento.
  • Datas estimadas: do item (seção PNCP) se houver; senão config.Provisorio.
"""

from __future__ import annotations

import time
import unicodedata

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from app_selectors import S, XPATHS
from logger import get_logger
from models import ItemContratacao
from utils_dom import js_set_value, wait_dom_stable

log = get_logger(__name__)
K = config.Constantes


# ----------------------------------------------------------------------- #
# Helpers internos
# ----------------------------------------------------------------------- #
def _normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem aspas tipográficas — para comparação."""
    n = unicodedata.normalize("NFD", str(texto or ""))
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    for a, b in (("“", '"'), ("”", '"'), ("’", "'"), ("‘", "'"), ('"', ""), ("'", "")):
        n = n.replace(a, b)
    return " ".join(n.split()).lower().strip()


def _formatar_data(data, use_mmdd: bool) -> str:
    """Aceita tupla (d, m, a) ou string 'dd/mm/aaaa' e devolve no formato do navegador."""
    if isinstance(data, tuple):
        dd, mm, yyyy = data
    else:
        dd, mm, yyyy = (int(x) for x in str(data).replace("-", "/").split("/")[:3])
    return f"{mm:02d}/{dd:02d}/{yyyy:04d}" if use_mmdd else f"{dd:02d}/{mm:02d}/{yyyy:04d}"


def _navegador_em_ingles(driver) -> bool:
    lang = (driver.execute_script(
        "return navigator.language || navigator.userLanguage || 'pt-BR';"
    ) or "pt-BR").lower()
    return lang.startswith("en")


def _digitar_data(driver, campo, valor: str) -> None:
    """Limpa e digita uma data num campo de calendário."""
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(Keys.DELETE)
    campo.send_keys(valor)
    campo.send_keys(Keys.ENTER)
    campo.send_keys(Keys.TAB)


def _data_inicio(item: ItemContratacao):
    """Data de início: do item (PNCP) se houver; senão fallback provisório."""
    return item.data_inicio_estimada or config.Provisorio.DATA_INICIAL


def _data_fim(item: ItemContratacao):
    return item.data_fim_estimada or config.Provisorio.DATA_FINAL


# ----------------------------------------------------------------------- #
# 1) Pré-cadastro (modal "Criar")
# ----------------------------------------------------------------------- #
def criar_contratacao(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Abre o modal de criação e preenche o pré-cadastro."""
    timeout = timeout or config.TIMEOUT
    w = WebDriverWait(driver, timeout)
    log.info("Abrindo modal de criação: %s", item.titulo)

    # Botão "Criar".
    btn = w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, S.CRIAR_BTN)))
    try:
        btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)  # modal abrir

    # Título (vem da planilha).
    w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.TITULO_INPUT)))
    js_set_value(driver, S.TITULO_INPUT, item.titulo, fire=True)

    # Categoria (dropdown).
    w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, S.CATEGORIA_TRIGGER))).click()
    wait_dom_stable(driver)
    w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, S.CATEGORIA_OPCAO_1))).click()
    wait_dom_stable(driver)

    # Datas estimadas (formato depende do idioma do navegador).
    use_mmdd = _navegador_em_ingles(driver)

    dt_inicio = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.DATA_INICIO_INPUT)))
    _digitar_data(driver, dt_inicio, _formatar_data(_data_inicio(item), use_mmdd))
    wait_dom_stable(driver)

    dt_fim = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.DATA_FIM_INPUT)))
    _digitar_data(driver, dt_fim, _formatar_data(_data_fim(item), use_mmdd))

    # Objeto (planilha) e Justificativa (constante).
    w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.DESCRICAO_TEXTAREA)))
    js_set_value(driver, S.DESCRICAO_TEXTAREA, item.objeto, fire=True)

    w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.JUSTIFICATIVA_TEXTAREA)))
    js_set_value(driver, S.JUSTIFICATIVA_TEXTAREA, K.JUSTIFICATIVA, fire=True)
    wait_dom_stable(driver)

    # Concluir e aguardar o modal fechar.
    w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, S.MODAL_CONCLUIR_BTN))).click()
    w.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, S.MODAL_CRIACAO)))
    log.info("Pré-cadastro concluído.")


# ----------------------------------------------------------------------- #
# 2) Localizar a contratação na grid e clicar em Editar
# ----------------------------------------------------------------------- #
def localizar_contratacao(driver, item: ItemContratacao, timeout: int = None) -> dict:
    """Casa o título (normalizado) na coluna 4 da grid e clica em Editar."""
    timeout = timeout or config.TIMEOUT
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, S.GRID_LINHAS))
    )

    alvo = _normalizar(item.titulo)
    log.info("Localizando contratação na grid: %s", item.titulo)

    for tr in driver.find_elements(By.CSS_SELECTOR, S.GRID_LINHAS):
        td4 = tr.find_element(By.CSS_SELECTOR, S.GRID_TITULO_CELULA)
        texto = _normalizar(td4.text or td4.get_attribute("innerText") or "")
        if alvo == texto or alvo in texto or texto in alvo:
            tr_id = tr.get_attribute("id") or ""
            btn = tr.find_element(By.CSS_SELECTOR, S.EDITAR_BTN_PREFIXO)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            driver.execute_script("arguments[0].click();", btn)
            log.info("Contratação localizada (%s) e aberta para edição.", tr_id)
            return {"tr_id": tr_id, "clicked_edit": True}

    raise TimeoutError(f"Título não localizado na coluna 4: {alvo}")


# ----------------------------------------------------------------------- #
# 3) Dados Básicos (processo + modalidade)
# ----------------------------------------------------------------------- #
def preencher_dados_basicos(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Preenche número do processo (planilha) e modalidade (constante)."""
    timeout = timeout or config.TIMEOUT
    w = WebDriverWait(driver, timeout)
    log.info("Preenchendo Dados Básicos (processo %s)...", item.processo)

    # Número do processo (idempotente: valida o valor aplicado).
    campo = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.PROCESSO_INPUT)))
    valor = str(item.processo or "").strip()
    js_set_value(driver, S.PROCESSO_INPUT, valor, fire=True)
    w.until(lambda d: (campo.get_attribute("value") or "").strip() == valor)

    # Tipo de Contratação (combobox PrimeNG).
    combo = w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, S.MODALIDADE_COMBO)))
    combo.click()
    lista = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.LISTBOX)))

    for op in lista.find_elements(By.CSS_SELECTOR, S.LISTBOX_OPCAO):
        if K.MODALIDADE_CONTEM in (op.text or "").strip().lower():
            op.click()
            break
    else:
        raise RuntimeError(f"Modalidade não encontrada: {K.MODALIDADE_CONTEM}")

    w.until(lambda d: K.MODALIDADE_CONTEM.split()[0] in (combo.text or "").lower())
    log.info("Dados Básicos preenchidos.")

    # NOTA: Fundamento Legal, Modo de disputa, Moeda, SRP e Info. Complementares
    # estão pré-preenchidos/bloqueados/opcionais no fluxo atual — ver _fundamento_legal().


def _fundamento_legal(driver, timeout: int = None) -> None:
    """
    (Desativado) Seleção do Fundamento Legal na árvore (config.Constantes.FUNDAMENTO_LEGAL).
    Os seletores eram posicionais (p-treenode:nth-child) e frágeis; só reabilitar
    após confirmar a estrutura atual da árvore.
    """
    raise NotImplementedError("Fundamento Legal ainda não reabilitado.")


# ----------------------------------------------------------------------- #
# Orquestração da aba
# ----------------------------------------------------------------------- #
def run(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Executa o Step A completo: pré-cadastro -> localizar -> dados básicos."""
    timeout = timeout or config.TIMEOUT
    criar_contratacao(driver, item, timeout)
    localizar_contratacao(driver, item, timeout)
    preencher_dados_basicos(driver, item, timeout)
