# page_dados_basicos.py
"""
Aba "Dados Básicos" do ComprasNet.

Responsabilidade desta page:
  1. Número do processo;
  2. Tipo de contratação;
  3. Fundamentação legal;
  4. Modo de disputa.

Esta page pressupõe que a contratação já está aberta em modo de edição.
Quem abre/localiza a contratação é page_dados_iniciais.py.
Quem decide a ordem é exclusivamente main.py.
"""

from __future__ import annotations

from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from app_selectors import S
from logger import get_logger
from models import ItemContratacao
from utils_dom import (
    js_set_value,
    wait_dom_stable,
    wclick,
)


log = get_logger(__name__)
K = config.Constantes


def preencher_dados_basicos(
    driver,
    item: ItemContratacao,
    timeout: int | None = None,
) -> None:
    timeout = timeout or config.TIMEOUT

    w = WebDriverWait(
        driver,
        timeout,
    )

    log.info(
        "Preenchendo Dados Básicos (processo %s)...",
        item.processo,
    )

    campo = w.until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                S.PROCESSO_INPUT,
            )
        )
    )

    valor = str(
        item.processo
        or ""
    ).strip()

    js_set_value(
        driver,
        S.PROCESSO_INPUT,
        valor,
        fire=True,
    )

    w.until(
        lambda d: (
            campo.get_attribute("value")
            or ""
        ).strip() == valor
    )

    _selecionar_dropdown(
        driver,
        S.TIPO_TRIGGER,
        K.TIPO_CONTRATACAO,
        timeout,
    )

    _selecionar_fundamento(
        driver,
        timeout,
    )

    _selecionar_modo_disputa(
        driver,
        timeout,
    )

    log.info(
        "Dados Básicos preenchidos."
    )


def _selecionar_dropdown(
    driver,
    trigger_css: str,
    label: str,
    timeout: int,
) -> None:
    wclick(
        driver,
        trigger_css,
        timeout,
    )

    wait_dom_stable(
        driver
    )

    wclick(
        driver,
        S.opcao_por_label(label),
        timeout,
    )

    wait_dom_stable(
        driver
    )


def _selecionar_fundamento(
    driver,
    timeout: int,
) -> None:
    log.info(
        "Selecionando fundamentação legal..."
    )

    wclick(
        driver,
        S.FUNDAMENTO_EDITAR_ICON,
        timeout,
    )

    WebDriverWait(
        driver,
        timeout,
    ).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                S.tree_no(
                    K.FUND_LEI
                ),
            )
        )
    )

    _garantir_expandido(
        driver,
        S.tree_no(
            K.FUND_LEI
        ),
        timeout,
    )

    _garantir_expandido(
        driver,
        S.tree_no(
            K.FUND_ARTIGO
        ),
        timeout,
    )

    no_inciso = WebDriverWait(
        driver,
        timeout,
    ).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                S.tree_no_prefixo(
                    K.FUND_INCISO_PREFIXO
                ),
            )
        )
    )

    conteudo = no_inciso.find_element(
        By.CSS_SELECTOR,
        "div.p-treenode-content",
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        conteudo,
    )

    driver.execute_script(
        "arguments[0].click();",
        conteudo,
    )

    wait_dom_stable(
        driver
    )

    wclick(
        driver,
        S.SALVAR_FUNDAMENTO_BTN,
        timeout,
    )

    wait_dom_stable(
        driver
    )


def _selecionar_modo_disputa(
    driver,
    timeout: int,
) -> None:
    log.info(
        "Selecionando modo de disputa..."
    )

    wait = WebDriverWait(
        driver,
        timeout,
    )

    combo_id = (
        "modo-disputa-contratacao"
    )

    combo = wait.until(
        EC.presence_of_element_located(
            (
                By.ID,
                combo_id,
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        combo,
    )

    if (
        combo.get_attribute(
            "aria-expanded"
        )
        or ""
    ).lower() != "true":
        driver.execute_script(
            "arguments[0].click();",
            combo,
        )

    wait.until(
        lambda d: (
            d.find_element(
                By.ID,
                combo_id,
            ).get_attribute(
                "aria-expanded"
            )
            or ""
        ).lower() == "true"
    )

    seletor_opcao = (
        f"li[role='option']"
        f"[aria-label='{K.MODO_DISPUTA}']"
        f"[data-p-disabled='false']"
    )

    def _opcao_visivel(d):
        for elemento in d.find_elements(
            By.CSS_SELECTOR,
            seletor_opcao,
        ):
            try:
                if elemento.is_displayed():
                    return elemento
            except Exception:
                continue

        return False

    opcao = wait.until(
        _opcao_visivel
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        opcao,
    )

    driver.execute_script(
        "arguments[0].click();",
        opcao,
    )

    wait.until(
        lambda d: (
            d.find_element(
                By.ID,
                combo_id,
            ).get_attribute(
                "aria-expanded"
            )
            or ""
        ).lower() == "false"
    )

    wait_dom_stable(
        driver
    )

    log.info(
        "Modo de disputa selecionado: %s",
        K.MODO_DISPUTA,
    )


def _garantir_expandido(
    driver,
    no_css: str,
    timeout: int,
) -> None:
    li = WebDriverWait(
        driver,
        timeout,
    ).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                no_css,
            )
        )
    )

    if (
        li.get_attribute(
            "aria-expanded"
        )
        or ""
    ).lower() != "true":
        toggler = li.find_element(
            By.CSS_SELECTOR,
            "div.p-treenode-content button.p-tree-toggler",
        )

        driver.execute_script(
            "arguments[0].click();",
            toggler,
        )

        wait_dom_stable(
            driver
        )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Executa Dados Básicos para UM processo.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum registro recebido em Dados Básicos."
        )

    item = itens_processo[0]

    preencher_dados_basicos(
        driver,
        item,
    )
