# page_dados_basicos.py
"""
Aba "Dados Básicos" (antigo step_a + getRecord), com seletores reais do ComprasNet.

Fluxo:
  1. criar_contratacao(item)   -> modal Criar: título, categoria (Serviços),
                                   data início (DATA_INICIO), data término (DATA_EMPENHO),
                                   objeto, justificativa (constante) -> Concluir.
  2. selecionar_pca(item)      -> escolhe "PCA {ano} - Em Execução" pelo ano de início.
  3. abrir_aba_minhas_uasg()   -> clica na aba "Contratações Minhas UASG".
  4. localizar_contratacao(item)-> na grid, casa TÍTULO + INÍCIO + CONCLUSÃO e clica Editar.
  5. preencher_dados_basicos(item)-> nº do processo + modalidade (a confirmar).

Fontes de dado:
  • Planilha (ItemContratacao): título=NOME_CURSO, objeto=OBJETO, processo=PROCESSO,
    início=DATA_INICIO, término=DATA_EMPENHO.
  • Constantes (config.Constantes): categoria (Serviços), justificativa, modalidade.
"""

from __future__ import annotations

import time
import unicodedata
from datetime import datetime
from typing import Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from app_selectors import S
from logger import get_logger
from models import ItemContratacao
from utils_dom import js_set_value, wait_dom_stable, wclick

log = get_logger(__name__)
K = config.Constantes


# ----------------------------------------------------------------------- #
# Datas
# ----------------------------------------------------------------------- #
def _parse_data(valor) -> Optional[Tuple[int, int, int]]:
    """
    Converte um valor de data em (dia, mês, ano).
    Aceita tupla, 'dd/mm/aaaa' e ISO ('2026-06-17' ou '2026-06-17 00:00:00').
    """
    if isinstance(valor, tuple) and len(valor) == 3:
        return tuple(int(x) for x in valor)  # type: ignore[return-value]

    s = str(valor or "").strip()
    if not s:
        return None
    s = s.split()[0]  # descarta a parte de hora do ISO

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s, fmt)
            return (d.day, d.month, d.year)
        except ValueError:
            continue
    log.warning("Data não reconhecida: %r", valor)
    return None


def _data_para_input(valor, use_mmdd: bool) -> str:
    """Formata a data para digitar no campo (dd/mm/aaaa ou mm/dd/aaaa por locale)."""
    dmy = _parse_data(valor)
    if not dmy:
        return ""
    dd, mm, yyyy = dmy
    return f"{mm:02d}/{dd:02d}/{yyyy:04d}" if use_mmdd else f"{dd:02d}/{mm:02d}/{yyyy:04d}"


def _data_ddmmaaaa(valor) -> str:
    """Formata a data como 'dd/mm/aaaa' (para comparar com o texto da grade)."""
    dmy = _parse_data(valor)
    if not dmy:
        return ""
    dd, mm, yyyy = dmy
    return f"{dd:02d}/{mm:02d}/{yyyy:04d}"


# ----------------------------------------------------------------------- #
# Helpers de texto / navegador
# ----------------------------------------------------------------------- #
def _normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem aspas tipográficas — para comparação."""
    n = unicodedata.normalize("NFD", str(texto or ""))
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    for a, b in (("“", '"'), ("”", '"'), ("’", "'"), ("‘", "'"), ('"', ""), ("'", "")):
        n = n.replace(a, b)
    return " ".join(n.split()).lower().strip()


def _navegador_em_ingles(driver) -> bool:
    lang = (driver.execute_script(
        "return navigator.language || navigator.userLanguage || 'pt-BR';"
    ) or "pt-BR").lower()
    return lang.startswith("en")


def _digitar_data(driver, campo, valor: str) -> None:
    """Limpa e digita uma data num campo de calendário (input mascarado)."""
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(Keys.DELETE)
    campo.send_keys(valor)
    campo.send_keys(Keys.ENTER)
    campo.send_keys(Keys.TAB)


# ----------------------------------------------------------------------- #
# 1) Pré-cadastro (modal "Criar")
# ----------------------------------------------------------------------- #
def criar_contratacao(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Abre o modal de criação e preenche o pré-cadastro; conclui ao final."""
    timeout = timeout or config.TIMEOUT
    w = WebDriverWait(driver, timeout)
    log.info("Criando contratação: %s", item.titulo)

    # Botão "Criar".
    wclick(driver, S.CRIAR_BTN, timeout)
    time.sleep(1)  # modal abrir

    # Título (planilha: NOME_CURSO).
    w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.TITULO_INPUT)))
    js_set_value(driver, S.TITULO_INPUT, item.titulo, fire=True)

    # Categoria — sempre "Serviços" (opção por aria-label, não pelo pn_id).
    wclick(driver, S.CATEGORIA_TRIGGER, timeout)
    wait_dom_stable(driver)
    wclick(driver, S.CATEGORIA_OPCAO_SERVICOS, timeout)
    wait_dom_stable(driver)

    use_mmdd = _navegador_em_ingles(driver)

    # Data de início (planilha: DATA_INICIO).
    dt_ini = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.DATA_INICIO_INPUT)))
    _digitar_data(driver, dt_ini, _data_para_input(item.data_inicio, use_mmdd))
    wait_dom_stable(driver)

    # Data de término (planilha: DATA_EMPENHO).
    dt_fim = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.DATA_FIM_INPUT)))
    _digitar_data(driver, dt_fim, _data_para_input(item.data_conclusao, use_mmdd))
    wait_dom_stable(driver)

    # Objeto (planilha: OBJETO) e Justificativa (constante).
    w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.DESCRICAO_TEXTAREA)))
    js_set_value(driver, S.DESCRICAO_TEXTAREA, item.objeto, fire=True)

    w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.JUSTIFICATIVA_TEXTAREA)))
    js_set_value(driver, S.JUSTIFICATIVA_TEXTAREA, K.JUSTIFICATIVA, fire=True)
    wait_dom_stable(driver)

    # Concluir (o botão só habilita quando o form valida; wclick espera ficar clicável).
    wclick(driver, S.CONCLUIR_BTN, timeout)
    wait_dom_stable(driver)
    log.info("Pré-cadastro concluído.")


# ----------------------------------------------------------------------- #
# 2) Selecionar PCA (ano)
# ----------------------------------------------------------------------- #
def _ano_pca(item: ItemContratacao) -> Optional[int]:
    """Ano do PCA = ano da data de início; se vazia, cai para a data de término."""
    dmy = _parse_data(item.data_inicio) or _parse_data(item.data_conclusao)
    return dmy[2] if dmy else None


def selecionar_pca(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Abre o dropdown de PCA e seleciona 'PCA {ano} - {status}'."""
    timeout = timeout or config.TIMEOUT
    ano = _ano_pca(item)
    if ano is None:
        raise RuntimeError("Não foi possível determinar o ano do PCA (datas vazias).")

    label = f"PCA {ano} - {K.PCA_STATUS}"
    log.info("Selecionando PCA: %s", label)
    wclick(driver, S.PCA_COMBO, timeout)
    wait_dom_stable(driver)
    wclick(driver, S.pca_opcao(label), timeout)
    wait_dom_stable(driver)


# ----------------------------------------------------------------------- #
# 3) Aba "Contratações Minhas UASG"
# ----------------------------------------------------------------------- #
def abrir_aba_minhas_uasg(driver, timeout: int = None) -> None:
    """Clica na aba que lista as contratações da própria UASG."""
    timeout = timeout or config.TIMEOUT
    log.info("Abrindo aba 'Contratações Minhas UASG'...")
    wclick(driver, S.TAB_MINHAS_UASG, timeout)
    wait_dom_stable(driver)


# ----------------------------------------------------------------------- #
# 4) Localizar na grid (título + início + conclusão) e clicar em Editar
# ----------------------------------------------------------------------- #
def localizar_contratacao(driver, item: ItemContratacao, timeout: int = None) -> dict:
    """
    Casa 3 campos na grid — TÍTULO, INÍCIO e CONCLUSÃO — para achar a linha certa
    (evita confundir contratações de mesmo título) e clica em Editar.
    """
    timeout = timeout or config.TIMEOUT
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, S.GRID_LINHAS))
    )

    alvo_titulo = _normalizar(item.titulo)
    alvo_inicio = _data_ddmmaaaa(item.data_inicio)
    alvo_concl = _data_ddmmaaaa(item.data_conclusao)
    log.info("Localizando: título='%s' | início=%s | conclusão=%s",
             item.titulo, alvo_inicio, alvo_concl)

    for tr in driver.find_elements(By.CSS_SELECTOR, S.GRID_LINHAS):
        titulo = _normalizar(_celula(tr, S.GRID_TITULO_CELULA))
        inicio = _celula(tr, S.GRID_INICIO_CELULA).strip()
        concl = _celula(tr, S.GRID_CONCLUSAO_CELULA).strip()

        titulo_ok = alvo_titulo == titulo or alvo_titulo in titulo or titulo in alvo_titulo
        if titulo_ok and inicio == alvo_inicio and concl == alvo_concl:
            tr_id = tr.get_attribute("id") or ""
            link = tr.find_element(By.CSS_SELECTOR, S.LINK_CONTRATACAO_CELULA)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
            driver.execute_script("arguments[0].click();", link)
            log.info("Contratação localizada (%s); abrindo pelo link.", tr_id)
            return {"tr_id": tr_id, "clicked_link": True}

    raise TimeoutError(
        f"Contratação não localizada (título='{item.titulo}', "
        f"início={alvo_inicio}, conclusão={alvo_concl})."
    )


def _celula(tr, css: str) -> str:
    """Texto de uma célula da linha (vazio se não existir)."""
    try:
        el = tr.find_element(By.CSS_SELECTOR, css)
        return el.text or el.get_attribute("innerText") or ""
    except Exception:
        return ""


# ----------------------------------------------------------------------- #
# 5) Abrir edição da contratação
# ----------------------------------------------------------------------- #
def abrir_edicao(driver, timeout: int = None) -> None:
    """Na tela de detalhe, clica em 'Editar contratação' (botão por texto)."""
    timeout = timeout or config.TIMEOUT
    log.info("Abrindo edição da contratação...")
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, XPATHS.botao_por_texto("Editar contratação")))
    ).click()
    wait_dom_stable(driver)


# ----------------------------------------------------------------------- #
# 6) Dados Básicos: processo + tipo + modo de disputa + fundamentação
# ----------------------------------------------------------------------- #
def preencher_dados_basicos(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Processo (planilha) + tipo, modo de disputa e fundamentação (constantes)."""
    timeout = timeout or config.TIMEOUT
    w = WebDriverWait(driver, timeout)
    log.info("Preenchendo Dados Básicos (processo %s)...", item.processo)

    # Número do processo.
    campo = w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, S.PROCESSO_INPUT)))
    valor = str(item.processo or "").strip()
    js_set_value(driver, S.PROCESSO_INPUT, valor, fire=True)
    w.until(lambda d: (campo.get_attribute("value") or "").strip() == valor)

    # Tipo de contratação (sempre "Dispensa de licitação").
    _selecionar_dropdown(driver, S.TIPO_TRIGGER, K.TIPO_CONTRATACAO, timeout)

    # Modo de disputa (sempre "Não se aplica").
    _selecionar_dropdown(driver, S.MODO_DISPUTA_TRIGGER, K.MODO_DISPUTA, timeout)

    # Fundamentação legal (LEI 14.133/2021 > Art. 75 > Inciso II).
    _selecionar_fundamento(driver, timeout)

    log.info("Dados Básicos preenchidos.")


def _selecionar_dropdown(driver, trigger_css: str, label: str, timeout: int) -> None:
    """Abre um p-dropdown pelo gatilho e escolhe a opção pelo aria-label."""
    wclick(driver, trigger_css, timeout)
    wait_dom_stable(driver)
    wclick(driver, S.opcao_por_label(label), timeout)
    wait_dom_stable(driver)


def _selecionar_fundamento(driver, timeout: int) -> None:
    """Abre a árvore de fundamentos e seleciona LEI 14.133/2021 > Art. 75 > Inciso II."""
    log.info("Selecionando fundamentação legal...")
    wclick(driver, S.FUNDAMENTO_EDITAR_ICON, timeout)

    # Aguarda a árvore renderizar.
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, S.tree_no(K.FUND_LEI)))
    )

    _garantir_expandido(driver, S.tree_no(K.FUND_LEI), timeout)
    _garantir_expandido(driver, S.tree_no(K.FUND_ARTIGO), timeout)

    # Seleciona o Inciso II (aria-label começa com 'Inciso II:').
    no_inciso = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, S.tree_no_prefixo(K.FUND_INCISO_PREFIXO)))
    )
    conteudo = no_inciso.find_element(By.CSS_SELECTOR, "div.p-treenode-content")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", conteudo)
    driver.execute_script("arguments[0].click();", conteudo)
    wait_dom_stable(driver)

    wclick(driver, S.SALVAR_FUNDAMENTO_BTN, timeout)
    wait_dom_stable(driver)


def _garantir_expandido(driver, no_css: str, timeout: int) -> None:
    """Expande um nó da árvore apenas se ainda estiver colapsado (evita re-colapsar)."""
    li = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, no_css))
    )
    if (li.get_attribute("aria-expanded") or "").lower() != "true":
        # O toggler do próprio nó é o primeiro em ordem de documento dentro do li.
        toggler = li.find_element(By.CSS_SELECTOR, "div.p-treenode-content button.p-tree-toggler")
        driver.execute_script("arguments[0].click();", toggler)
        wait_dom_stable(driver)


# ----------------------------------------------------------------------- #
# Orquestração da aba
# ----------------------------------------------------------------------- #
def run(driver, item: ItemContratacao, timeout: int = None) -> None:
    """Executa o Step A completo."""
    timeout = timeout or config.TIMEOUT
    criar_contratacao(driver, item, timeout)
    selecionar_pca(driver, item, timeout)
    abrir_aba_minhas_uasg(driver, timeout)
    localizar_contratacao(driver, item, timeout)
    abrir_edicao(driver, timeout)
    preencher_dados_basicos(driver, item, timeout)
