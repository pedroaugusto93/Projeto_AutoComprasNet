# page_responsaveis.py
"""
Aba "5. Responsáveis" do ComprasNet.

Fluxo:
  1. Abre "5. Responsáveis".
  2. Clica em "Adicionar".
  3. Preenche CPF.
  4. Aguarda o ComprasNet carregar automaticamente o Nome.
  5. Preenche Email.
  6. Seleciona Cargo/Função.
  7. Preenche Despacho.
  8. Clica em "Adicionar".

Dados esperados na planilha:
  - resp_cpf
  - resp_email
  - resp_cargo
  - resp_despacho
"""

from __future__ import annotations

import re
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


ABA_RESPONSAVEIS = (
    By.XPATH,
    "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
    "[.//span[normalize-space(.)='5. Responsáveis']]",
)

BTN_CRIAR_RESPONSAVEL = (
    By.ID,
    "criar-responsavel",
)

CPF_RESPONSAVEL = (
    By.ID,
    "cpf-responsavel",
)

NOME_RESPONSAVEL = (
    By.ID,
    "nome-responsavel",
)

EMAIL_RESPONSAVEL = (
    By.ID,
    "email-responsavel",
)

CARGO_FUNCAO_COMBO = (
    By.CSS_SELECTOR,
    "p-dropdown#cargo-funcao-responsavel "
    "span[role='combobox'][aria-labelledby='label-cargo-funcao-responsavel']",
)

DESPACHO_RESPONSAVEL = (
    By.ID,
    "despacho-responsavel",
)

BTN_SALVAR_RESPONSAVEL = (
    By.ID,
    "salvar-responsavel",
)


def _wait(driver, timeout: int | None = None) -> WebDriverWait:
    return WebDriverWait(
        driver,
        timeout or TIMEOUT,
    )


def _click(driver, locator, timeout: int | None = None):
    """Clique robusto com scroll e fallback JavaScript."""
    w = _wait(
        driver,
        timeout,
    )

    el = w.until(
        EC.presence_of_element_located(
            locator
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        el,
    )

    try:
        el = w.until(
            EC.element_to_be_clickable(
                locator
            )
        )
        el.click()

    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        el = w.until(
            EC.presence_of_element_located(
                locator
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            el,
        )

    return el


def _preencher(driver, locator, valor: str) -> str:
    """Limpa, preenche e dispara blur com TAB."""
    elemento = _wait(
        driver
    ).until(
        EC.visibility_of_element_located(
            locator
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        elemento,
    )

    elemento.click()
    elemento.send_keys(
        Keys.CONTROL,
        "a",
    )
    elemento.send_keys(
        Keys.DELETE
    )
    elemento.send_keys(
        str(valor)
    )
    elemento.send_keys(
        Keys.TAB
    )

    return (
        elemento.get_attribute(
            "value"
        )
        or ""
    ).strip()


def _somente_digitos(valor: str) -> str:
    return re.sub(
        r"\D+",
        "",
        str(valor or ""),
    )


def _formatar_cpf(valor: str) -> str:
    digitos = _somente_digitos(
        valor
    )

    if len(digitos) != 11:
        return valor

    return (
        f"{digitos[0:3]}."
        f"{digitos[3:6]}."
        f"{digitos[6:9]}-"
        f"{digitos[9:11]}"
    )


def _processo_do_item(item: ItemContratacao) -> str:
    return str(
        getattr(
            item,
            "processo",
            None,
        )
        or getattr(
            item,
            "PROCESSO",
            None,
        )
        or ""
    ).strip()


def _valor_unico(
    itens_processo: List[ItemContratacao],
    atributo: str,
) -> str:
    """
    Retorna um único valor do processo e bloqueia dados conflitantes
    entre linhas da mesma contratação.
    """
    valores = []

    for item in itens_processo:
        valor = str(
            getattr(
                item,
                atributo,
                "",
            )
            or ""
        ).strip()

        if valor and valor not in valores:
            valores.append(
                valor
            )

    if not valores:
        raise RuntimeError(
            f"O campo {atributo} está vazio para o processo atual."
        )

    if len(valores) > 1:
        raise RuntimeError(
            f"O processo possui mais de um valor para {atributo}: "
            + " | ".join(
                valores
            )
        )

    return valores[0]


def _abrir_aba_responsaveis(driver) -> None:
    log.info(
        "Abrindo aba '5. Responsáveis'..."
    )

    _click(
        driver,
        ABA_RESPONSAVEIS,
    )

    wait_dom_stable(
        driver
    )

    _wait(
        driver
    ).until(
        EC.presence_of_element_located(
            BTN_CRIAR_RESPONSAVEL
        )
    )

    log.info(
        "Aba '5. Responsáveis' aberta."
    )


def _responsavel_ja_existe(driver, cpf: str) -> bool:
    """
    Evita recadastrar o CPF caso a etapa seja executada novamente
    durante os testes.
    """
    cpf_formatado = _formatar_cpf(
        cpf
    )

    try:
        texto = (
            driver.find_element(
                By.TAG_NAME,
                "body",
            ).text
            or ""
        )
    except Exception:
        return False

    return cpf_formatado in texto


def _abrir_modal(driver) -> None:
    log.info(
        "Clicando em 'Adicionar' responsável..."
    )

    _click(
        driver,
        BTN_CRIAR_RESPONSAVEL,
    )

    wait_dom_stable(
        driver
    )

    _wait(
        driver
    ).until(
        EC.visibility_of_element_located(
            CPF_RESPONSAVEL
        )
    )

    log.info(
        "Modal 'Adicionar responsável' aberto."
    )


def _preencher_cpf_e_aguardar_nome(driver, cpf: str) -> str:
    log.info(
        "Preenchendo CPF do responsável..."
    )

    _preencher(
        driver,
        CPF_RESPONSAVEL,
        cpf,
    )

    def nome_carregado(d):
        try:
            campo = d.find_element(
                *NOME_RESPONSAVEL
            )

            valor = (
                campo.get_attribute(
                    "value"
                )
                or ""
            ).strip()

            return valor if valor else False

        except StaleElementReferenceException:
            return False

    try:
        nome = _wait(
            driver
        ).until(
            nome_carregado
        )

    except TimeoutException as exc:
        raise RuntimeError(
            "O CPF foi preenchido, mas o ComprasNet não carregou "
            "automaticamente o Nome do responsável."
        ) from exc

    log.info(
        "Responsável identificado: %s",
        nome,
    )

    return str(
        nome
    )


def _selecionar_cargo(driver, cargo: str) -> None:
    log.info(
        "Selecionando Cargo/Função: %s",
        cargo,
    )

    combo = _wait(
        driver
    ).until(
        EC.element_to_be_clickable(
            CARGO_FUNCAO_COMBO
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        combo,
    )

    atual = (
        combo.text
        or combo.get_attribute(
            "aria-label"
        )
        or ""
    ).strip()

    if atual == cargo:
        return

    try:
        combo.click()

    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        combo = _wait(
            driver
        ).until(
            EC.presence_of_element_located(
                CARGO_FUNCAO_COMBO
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            combo,
        )

    def localizar_opcao(d):
        for opcao in d.find_elements(
            By.CSS_SELECTOR,
            "li[role='option']",
        ):
            try:
                if not opcao.is_displayed():
                    continue

                texto = (
                    opcao.get_attribute(
                        "aria-label"
                    )
                    or opcao.text
                    or ""
                ).strip()

                if texto == cargo:
                    return opcao

            except StaleElementReferenceException:
                continue

        return False

    try:
        opcao = _wait(
            driver
        ).until(
            localizar_opcao
        )

    except TimeoutException as exc:
        raise RuntimeError(
            f"Cargo/Função não encontrado: {cargo!r}. "
            "O valor de resp_cargo deve ser exatamente igual "
            "ao texto exibido pelo ComprasNet."
        ) from exc

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'nearest'});",
        opcao,
    )

    try:
        opcao.click()

    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        driver.execute_script(
            "arguments[0].click();",
            opcao,
        )

    wait_dom_stable(
        driver
    )

    log.info(
        "Cargo/Função selecionado."
    )


def _salvar(driver) -> None:
    """
    Operação de gravação: apenas um clique no botão final para evitar
    duplicidade caso a resposta visual do ComprasNet demore.
    """
    log.info(
        "Confirmando inclusão do responsável..."
    )

    botao = _wait(
        driver
    ).until(
        EC.element_to_be_clickable(
            BTN_SALVAR_RESPONSAVEL
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        botao,
    )

    botao.click()

    def modal_fechou(d):
        for elemento in d.find_elements(
            *BTN_SALVAR_RESPONSAVEL
        ):
            try:
                if elemento.is_displayed():
                    return False
            except StaleElementReferenceException:
                continue

        return True

    try:
        _wait(
            driver
        ).until(
            modal_fechou
        )

    except TimeoutException as exc:
        raise RuntimeError(
            "O botão 'Adicionar' foi acionado, mas o modal permaneceu aberto. "
            "Verifique se o ComprasNet exibiu alguma validação."
        ) from exc

    wait_dom_stable(
        driver
    )

    log.info(
        "Responsável incluído."
    )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Executa a etapa Responsáveis para UM ÚNICO processo.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum registro recebido em Responsáveis."
        )

    processos = {
        _processo_do_item(
            item
        )
        for item in itens_processo
        if _processo_do_item(
            item
        )
    }

    if len(processos) != 1:
        raise RuntimeError(
            "Responsáveis recebeu registros de mais de um processo: "
            + ", ".join(
                sorted(
                    processos
                )
            )
        )

    processo = next(
        iter(
            processos
        )
    )

    cpf = _somente_digitos(
        _valor_unico(
            itens_processo,
            "resp_cpf",
        )
    )

    email = _valor_unico(
        itens_processo,
        "resp_email",
    )

    cargo = _valor_unico(
        itens_processo,
        "resp_cargo",
    )

    despacho = _valor_unico(
        itens_processo,
        "resp_despacho",
    )

    if len(cpf) != 11:
        raise RuntimeError(
            f"CPF do responsável inválido: {cpf!r}. "
            "Esperados 11 dígitos."
        )

    if len(despacho) > 200:
        raise RuntimeError(
            "resp_despacho possui mais de 200 caracteres."
        )

    log.info(
        "▶ RESPONSÁVEIS | processo=%s | cpf=%s",
        processo,
        _formatar_cpf(
            cpf
        ),
    )

    _abrir_aba_responsaveis(
        driver
    )

    if _responsavel_ja_existe(
        driver,
        cpf,
    ):
        log.warning(
            "Responsável %s já aparece na página. Inclusão ignorada.",
            _formatar_cpf(
                cpf
            ),
        )
        return

    _abrir_modal(
        driver
    )

    _preencher_cpf_e_aguardar_nome(
        driver,
        cpf,
    )

    log.info(
        "Preenchendo e-mail..."
    )

    _preencher(
        driver,
        EMAIL_RESPONSAVEL,
        email,
    )

    _selecionar_cargo(
        driver,
        cargo,
    )

    log.info(
        "Preenchendo despacho..."
    )

    _preencher(
        driver,
        DESPACHO_RESPONSAVEL,
        despacho,
    )

    _salvar(
        driver
    )

    log.info(
        "✓ Responsável incluído para o processo %s.",
        processo,
    )
