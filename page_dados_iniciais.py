# page_dados_iniciais.py
"""
Criação inicial da contratação no ComprasNet.

Responsabilidade exclusiva:
  - abrir o modal "Criar";
  - preencher título;
  - selecionar categoria Serviços;
  - preencher data de início;
  - preencher data de término;
  - preencher objeto;
  - preencher justificativa;
  - concluir o pré-cadastro.

Esta page NÃO:
  - seleciona PCA;
  - procura contratação;
  - abre edição;
  - preenche Dados Básicos.

Essas responsabilidades ficam separadas para permitir reaproveitamento
no futuro fluxo de Atualização.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import List, Optional, Tuple

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


def _parse_data(valor) -> Optional[Tuple[int, int, int]]:
    if isinstance(valor, tuple) and len(valor) == 3:
        return tuple(int(x) for x in valor)

    s = str(valor or "").strip()

    if not s:
        return None

    s = s.split()[0]

    for fmt in (
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ):
        try:
            d = datetime.strptime(s, fmt)
            return d.day, d.month, d.year
        except ValueError:
            continue

    log.warning(
        "Data não reconhecida: %r",
        valor,
    )
    return None


def _data_para_input(
    valor,
    use_mmdd: bool,
) -> str:
    dmy = _parse_data(valor)

    if not dmy:
        return ""

    dd, mm, yyyy = dmy

    if use_mmdd:
        return f"{mm:02d}/{dd:02d}/{yyyy:04d}"

    return f"{dd:02d}/{mm:02d}/{yyyy:04d}"


def _navegador_em_ingles(driver) -> bool:
    lang = (
        driver.execute_script(
            "return navigator.language || navigator.userLanguage || 'pt-BR';"
        )
        or "pt-BR"
    ).lower()

    return lang.startswith("en")


def _digitar_data(
    campo,
    valor: str,
) -> None:
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(Keys.DELETE)
    campo.send_keys(valor)
    campo.send_keys(Keys.ENTER)
    campo.send_keys(Keys.TAB)


def criar_contratacao(
    driver,
    item: ItemContratacao,
    timeout: int | None = None,
) -> None:
    timeout = timeout or config.TIMEOUT
    wait = WebDriverWait(
        driver,
        timeout,
    )

    log.info(
        "Criando contratação: %s",
        item.titulo,
    )

    # Criar
    wclick(
        driver,
        S.CRIAR_BTN,
        timeout,
    )

    time.sleep(1)

    # Título
    wait.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                S.TITULO_INPUT,
            )
        )
    )

    js_set_value(
        driver,
        S.TITULO_INPUT,
        item.titulo,
        fire=True,
    )

    # Categoria = Serviços
    wclick(
        driver,
        S.CATEGORIA_TRIGGER,
        timeout,
    )
    wait_dom_stable(driver)

    wclick(
        driver,
        S.CATEGORIA_OPCAO_SERVICOS,
        timeout,
    )
    wait_dom_stable(driver)

    use_mmdd = _navegador_em_ingles(
        driver
    )

    # Data início
    campo_inicio = wait.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                S.DATA_INICIO_INPUT,
            )
        )
    )

    _digitar_data(
        campo_inicio,
        _data_para_input(
            item.data_inicio,
            use_mmdd,
        ),
    )

    wait_dom_stable(driver)

    # Data término
    campo_fim = wait.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                S.DATA_FIM_INPUT,
            )
        )
    )

    _digitar_data(
        campo_fim,
        _data_para_input(
            item.data_conclusao,
            use_mmdd,
        ),
    )

    wait_dom_stable(driver)

    # Objeto
    wait.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                S.DESCRICAO_TEXTAREA,
            )
        )
    )

    js_set_value(
        driver,
        S.DESCRICAO_TEXTAREA,
        item.objeto,
        fire=True,
    )

    # Justificativa
    wait.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                S.JUSTIFICATIVA_TEXTAREA,
            )
        )
    )

    js_set_value(
        driver,
        S.JUSTIFICATIVA_TEXTAREA,
        K.JUSTIFICATIVA,
        fire=True,
    )

    wait_dom_stable(driver)

    # Concluir
    wclick(
        driver,
        S.CONCLUIR_BTN,
        timeout,
    )

    wait_dom_stable(driver)

    log.info(
        "Pré-cadastro concluído."
    )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Cria a contratação correspondente a UM processo.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum registro recebido em Dados Iniciais."
        )

    item = itens_processo[0]

    log.info(
        "▶ DADOS INICIAIS | processo=%s",
        item.processo,
    )

    criar_contratacao(
        driver,
        item,
    )

    log.info(
        "✓ Dados iniciais concluídos para o processo %s.",
        item.processo,
    )
