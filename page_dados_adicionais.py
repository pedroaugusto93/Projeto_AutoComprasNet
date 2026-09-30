# page_dados_adicionais.py
"""
Aba "2. Dados adicionais da contratação".

Fluxo desta page:
  1. Abre "2. Dados adicionais da contratação".
  2. Expande "Endereço do Processo Eletrônico", se estiver recolhido.
  3. Marca "Sim" para processo eletrônico.
  4. Preenche o link com a coluna `processoLink` do Excel.
  5. Expande "Recurso Orçamentário da Contratação", se estiver recolhido.
  6. Seleciona "Estadual" em Tipo de Recurso.

A implementação é idempotente:
- se o fieldset já estiver aberto, não clica novamente;
- se "Sim" já estiver marcado, não desmarca;
- se o link já estiver correto, não reescreve;
- se "Estadual" já estiver selecionado, não clica novamente.
"""

from __future__ import annotations

from typing import List

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from logger import get_logger
from models import ItemContratacao
from utils_dom import wait_dom_stable


log = get_logger(__name__)
TIMEOUT = config.TIMEOUT


ABA_DADOS_ADICIONAIS = (
    By.XPATH,
    "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
    "[.//span[normalize-space(.)='2. Dados adicionais da contratação']]",
)

CHECK_PROCESSO_SIM = (By.ID, "checkbox-tem-link-processo")
LABEL_PROCESSO_SIM = (
    By.CSS_SELECTOR,
    "label[for='checkbox-tem-link-processo']",
)
INPUT_PROCESSO_LINK = (
    By.ID,
    "processo-eletronico-contratacao",
)

LABEL_TIPO_RECURSO = (
    By.ID,
    "label-tipo-recurso-contratacao",
)

OPCAO_ESTADUAL = (
    By.XPATH,
    "//li[@role='option' and "
    "(@aria-label='Estadual' or .//span[normalize-space(.)='Estadual'])]",
)


def _wait(driver, timeout: int | None = None) -> WebDriverWait:
    return WebDriverWait(driver, timeout or TIMEOUT)


def _click(driver, locator, timeout: int | None = None):
    w = _wait(driver, timeout)

    el = w.until(
        EC.presence_of_element_located(locator)
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        el,
    )

    try:
        el = w.until(
            EC.element_to_be_clickable(locator)
        )
        el.click()
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        el = w.until(
            EC.presence_of_element_located(locator)
        )
        driver.execute_script(
            "arguments[0].click();",
            el,
        )

    return el


def _fieldset_por_titulo(driver, titulo: str):
    """
    Localiza o <fieldset> que contém exatamente o título informado.
    """
    xpath = (
        "//fieldset[contains(@class,'collapsible')]"
        "[.//legend[normalize-space("
        "text()[normalize-space()]"
        f")='{titulo}']]"
    )

    # O XPath acima pode variar por causa dos spans internos do legend.
    # Fallback mais simples usando normalize-space(.) no próprio legend.
    xpath_fallback = (
        "//fieldset[contains(@class,'collapsible')]"
        f"[.//legend[contains(normalize-space(.), '{titulo}')]]"
    )

    try:
        return _wait(driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, xpath)
            )
        )
    except TimeoutException:
        return _wait(driver).until(
            EC.presence_of_element_located(
                (By.XPATH, xpath_fallback)
            )
        )


def _expandir_fieldset(driver, titulo: str):
    """
    Expande um fieldset somente se ele estiver recolhido.

    Estado observado no ComprasNet:
      recolhido -> div.fieldset-header[aria-label='Expandir']
      aberto    -> div.fieldset-header[aria-label='Recolher']
    """
    fieldset = _fieldset_por_titulo(
        driver,
        titulo,
    )

    header = fieldset.find_element(
        By.CSS_SELECTOR,
        "div.fieldset-header",
    )

    estado = (
        header.get_attribute("aria-label")
        or ""
    ).strip().lower()

    if estado == "expandir":
        log.info(
            "Expandindo bloco '%s'...",
            titulo,
        )

        legend = header.find_element(
            By.TAG_NAME,
            "legend",
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            legend,
        )

        try:
            legend.click()
        except Exception:
            driver.execute_script(
                "arguments[0].click();",
                legend,
            )

    def conteudo_aberto(d):
        try:
            fs = _fieldset_por_titulo(
                d,
                titulo,
            )
            hd = fs.find_element(
                By.CSS_SELECTOR,
                "div.fieldset-header",
            )
            estado_atual = (
                hd.get_attribute("aria-label")
                or ""
            ).strip().lower()

            contents = fs.find_elements(
                By.CSS_SELECTOR,
                ":scope > div.content",
            )

            conteudo_visivel = any(
                c.is_displayed()
                for c in contents
            )

            return fs if (
                estado_atual != "expandir"
                and conteudo_visivel
            ) else False

        except Exception:
            return False

    fieldset = _wait(driver).until(
        conteudo_aberto
    )

    log.info(
        "Bloco '%s' aberto.",
        titulo,
    )

    return fieldset


def _abrir_aba(driver) -> None:
    log.info(
        "Abrindo aba '2. Dados adicionais da contratação'..."
    )

    _click(
        driver,
        ABA_DADOS_ADICIONAIS,
    )

    wait_dom_stable(driver)

    _wait(driver).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//legend[contains(normalize-space(.), "
                "'Endereço do Processo Eletrônico')]",
            )
        )
    )

    log.info(
        "Aba '2. Dados adicionais da contratação' aberta."
    )


def _processo_do_item(item: ItemContratacao) -> str:
    return str(
        getattr(item, "processo", "")
        or getattr(item, "PROCESSO", "")
        or ""
    ).strip()


def _link_do_item(item: ItemContratacao) -> str:
    valor = (
        getattr(item, "processoLink", None)
        or getattr(item, "processo_link", None)
        or ""
    )

    if not valor:
        extras = getattr(item, "extras", {}) or {}
        valor = (
            extras.get("processoLink")
            or extras.get("PROCESSOLINK")
            or extras.get("processolink")
            or ""
        )

    return str(valor).strip()


def _obter_link_processo(
    itens_processo: List[ItemContratacao],
) -> str:
    links = {
        _link_do_item(item)
        for item in itens_processo
        if _link_do_item(item)
    }

    if not links:
        processo = (
            _processo_do_item(itens_processo[0])
            if itens_processo
            else ""
        )
        raise RuntimeError(
            "A coluna 'processoLink' está vazia para o processo "
            f"{processo or '(sem número)'}."
        )

    if len(links) > 1:
        raise RuntimeError(
            "Foram encontrados links diferentes na coluna 'processoLink' "
            "para o mesmo processo: "
            + " | ".join(sorted(links))
        )

    return next(iter(links))


def _marcar_processo_eletronico_sim(
    driver,
) -> None:
    _expandir_fieldset(
        driver,
        "Endereço do Processo Eletrônico",
    )

    check = _wait(driver).until(
        EC.presence_of_element_located(
            CHECK_PROCESSO_SIM
        )
    )

    marcado = (
        check.get_attribute("aria-checked")
        or ""
    ).lower() == "true"

    if not marcado:
        log.info(
            "Marcando 'Sim' para processo eletrônico..."
        )

        # O input do PrimeNG é oculto; o label é o alvo mais seguro.
        _click(
            driver,
            LABEL_PROCESSO_SIM,
        )

        _wait(driver).until(
            lambda d: (
                d.find_element(*CHECK_PROCESSO_SIM)
                .get_attribute("aria-checked")
                or ""
            ).lower() == "true"
        )
    else:
        log.info(
            "'Sim' para processo eletrônico já está marcado."
        )

    _wait(driver).until(
        EC.visibility_of_element_located(
            INPUT_PROCESSO_LINK
        )
    )


def _preencher_link(
    driver,
    link: str,
) -> None:
    campo = _wait(driver).until(
        EC.visibility_of_element_located(
            INPUT_PROCESSO_LINK
        )
    )

    atual = (
        campo.get_attribute("value")
        or ""
    ).strip()

    if atual == link:
        log.info(
            "Link do processo eletrônico já está preenchido corretamente."
        )
        return

    log.info(
        "Preenchendo link do processo eletrônico..."
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        campo,
    )

    campo.click()
    campo.send_keys(
        Keys.CONTROL,
        "a",
    )
    campo.send_keys(
        Keys.DELETE,
    )
    campo.send_keys(
        link,
    )
    campo.send_keys(
        Keys.TAB,
    )

    try:
        _wait(driver, 5).until(
            lambda d: (
                d.find_element(*INPUT_PROCESSO_LINK)
                .get_attribute("value")
                or ""
            ).strip() == link
        )
    except TimeoutException:
        # Fallback para Angular caso a digitação normal não seja absorvida.
        campo = _wait(driver).until(
            EC.presence_of_element_located(
                INPUT_PROCESSO_LINK
            )
        )

        driver.execute_script(
            """
            const el = arguments[0];
            const value = arguments[1];

            const setter = Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                'value'
            ).set;

            setter.call(el, value);
            el.dispatchEvent(new Event('input',  {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur',   {bubbles:true}));
            """,
            campo,
            link,
        )

        _wait(driver).until(
            lambda d: (
                d.find_element(*INPUT_PROCESSO_LINK)
                .get_attribute("value")
                or ""
            ).strip() == link
        )

    log.info(
        "Link do processo eletrônico preenchido."
    )


def _abrir_multiselect_tipo_recurso(
    driver,
):
    """
    Localiza o multiselect relacionado ao label 'Tipo de Recurso'.

    Usa classe-token exata 'p-multiselect', para não confundir com
    'p-multiselect-label-container'.
    """
    label = _wait(driver).until(
        EC.visibility_of_element_located(
            LABEL_TIPO_RECURSO
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        label,
    )

    root_xpath = (
        "//*[@id='label-tipo-recurso-contratacao']"
        "/following::div["
        "contains(concat(' ', normalize-space(@class), ' '), "
        "' p-multiselect ')"
        "][1]"
    )

    root = _wait(driver).until(
        EC.presence_of_element_located(
            (By.XPATH, root_xpath)
        )
    )

    try:
        root.click()
    except Exception:
        driver.execute_script(
            "arguments[0].click();",
            root,
        )

    return root


def _selecionar_recurso_estadual(
    driver,
) -> None:
    _expandir_fieldset(
        driver,
        "Recurso Orçamentário da Contratação",
    )

    _abrir_multiselect_tipo_recurso(
        driver,
    )

    opcao = _wait(driver).until(
        EC.visibility_of_element_located(
            OPCAO_ESTADUAL
        )
    )

    selecionado = (
        (opcao.get_attribute("aria-selected") or "").lower() == "true"
        or (opcao.get_attribute("aria-checked") or "").lower() == "true"
        or "p-highlight" in (
            opcao.get_attribute("class")
            or ""
        )
    )

    if not selecionado:
        log.info(
            "Selecionando Tipo de Recurso: Estadual..."
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'nearest'});",
            opcao,
        )

        try:
            opcao.click()
        except Exception:
            driver.execute_script(
                "arguments[0].click();",
                opcao,
            )

        def estadual_marcado(d):
            try:
                el = d.find_element(
                    *OPCAO_ESTADUAL
                )
                return (
                    (el.get_attribute("aria-selected") or "").lower() == "true"
                    or (el.get_attribute("aria-checked") or "").lower() == "true"
                    or "p-highlight" in (
                        el.get_attribute("class")
                        or ""
                    )
                    or bool(
                        el.find_elements(
                            By.CSS_SELECTOR,
                            ".p-checkbox-box.p-highlight",
                        )
                    )
                )
            except Exception:
                return False

        _wait(driver).until(
            estadual_marcado
        )
    else:
        log.info(
            "Tipo de Recurso 'Estadual' já está selecionado."
        )

    # Fecha o overlay sem alterar a seleção.
    try:
        driver.find_element(
            By.TAG_NAME,
            "body",
        ).send_keys(Keys.ESCAPE)
    except Exception:
        pass

    wait_dom_stable(driver)

    log.info(
        "Tipo de Recurso 'Estadual' confirmado."
    )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Executa Dados Adicionais para UM processo.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum item recebido em Dados Adicionais."
        )

    processos = {
        _processo_do_item(item)
        for item in itens_processo
        if _processo_do_item(item)
    }

    if len(processos) != 1:
        raise RuntimeError(
            "Dados Adicionais recebeu registros de mais de um processo: "
            + ", ".join(sorted(processos))
        )

    processo = next(iter(processos))
    link = _obter_link_processo(
        itens_processo
    )

    log.info(
        "▶ DADOS ADICIONAIS | processo=%s",
        processo,
    )

    _abrir_aba(
        driver,
    )

    _marcar_processo_eletronico_sim(
        driver,
    )

    _preencher_link(
        driver,
        link,
    )

    _selecionar_recurso_estadual(
        driver,
    )

    log.info(
        "✓ Dados adicionais concluídos para o processo %s.",
        processo,
    )
