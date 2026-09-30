# page_responsaveis.py
"""
Aba "5. Responsáveis" do ComprasNet.

Cadastra, em sequência e com salvamento independente:

1) Responsável pela contratação direta
   - CPF: resp_cpf
   - Email: resp_email
   - Despacho: resp_despacho
   - Cargo/Função fixo: "Responsável pela contratação direta"

2) Autoridade competente
   - CPF: autoridade_cpf
   - Email: autoridade_email (se existir)
   - Despacho: autoridade_despacho (se existir)
   - Cargo/Função fixo: "Autoridade competente"

Sequência obrigatória de cada cadastro:
  #criar-responsavel
      -> preencher
      -> #salvar-responsavel
      -> aguardar modal fechar

Somente depois começa o próximo cadastro, clicando novamente
em #criar-responsavel.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
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

CARGO_RESPONSAVEL = "Responsável pela contratação direta"
CARGO_AUTORIDADE = "Autoridade competente"


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


@dataclass(frozen=True)
class DadosResponsavel:
    cpf: str
    email: str
    despacho: str
    cargo: str
    rotulo: str


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

    if valor:
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
    *,
    obrigatorio: bool = True,
) -> str:
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
        if obrigatorio:
            raise RuntimeError(
                f"O campo {atributo} está vazio para o processo atual."
            )

        return ""

    if len(valores) > 1:
        raise RuntimeError(
            f"O processo possui mais de um valor para {atributo}: "
            + " | ".join(
                valores
            )
        )

    return valores[0]


def _obter_cadastros(
    itens_processo: List[ItemContratacao],
) -> List[DadosResponsavel]:

    responsavel = DadosResponsavel(
        cpf=_somente_digitos(
            _valor_unico(
                itens_processo,
                "resp_cpf",
            )
        ),
        email=_valor_unico(
            itens_processo,
            "resp_email",
        ),
        despacho=_valor_unico(
            itens_processo,
            "resp_despacho",
        ),
        cargo=CARGO_RESPONSAVEL,
        rotulo="Responsável pela contratação direta",
    )

    autoridade = DadosResponsavel(
        cpf=_somente_digitos(
            _valor_unico(
                itens_processo,
                "autoridade_cpf",
            )
        ),
        email=_valor_unico(
            itens_processo,
            "autoridade_email",
            obrigatorio=False,
        ),
        despacho=_valor_unico(
            itens_processo,
            "autoridade_despacho",
            obrigatorio=False,
        ),
        cargo=CARGO_AUTORIDADE,
        rotulo="Autoridade competente",
    )

    for dados in (
        responsavel,
        autoridade,
    ):
        if len(dados.cpf) != 11:
            raise RuntimeError(
                f"CPF inválido para {dados.rotulo}: {dados.cpf!r}. "
                "Esperados 11 dígitos."
            )

        if len(dados.despacho) > 200:
            raise RuntimeError(
                f"Despacho de {dados.rotulo} possui mais de 200 caracteres."
            )

    return [
        responsavel,
        autoridade,
    ]


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


def _cpf_ja_existe(driver, cpf: str) -> bool:
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


def _abrir_modal(driver, rotulo: str) -> None:
    """
    Inicia um cadastro NOVO clicando no botão externo:
    #criar-responsavel.
    """
    log.info(
        "%s | clicando em #criar-responsavel...",
        rotulo,
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
        "%s | modal aberto.",
        rotulo,
    )


def _preencher_cpf_e_aguardar_nome(
    driver,
    cpf: str,
    rotulo: str,
) -> str:
    log.info(
        "%s | preenchendo CPF %s...",
        rotulo,
        _formatar_cpf(
            cpf
        ),
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
            f"{rotulo}: o CPF foi preenchido, mas o ComprasNet "
            "não carregou automaticamente o Nome."
        ) from exc

    log.info(
        "%s | nome carregado: %s",
        rotulo,
        nome,
    )

    return str(
        nome
    )


def _selecionar_cargo(
    driver,
    cargo: str,
) -> None:
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
        log.info(
            "Cargo/Função já selecionado: %s",
            cargo,
        )
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
            f"Cargo/Função não encontrado no ComprasNet: {cargo!r}."
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
        opcao = _wait(
            driver
        ).until(
            localizar_opcao
        )

        driver.execute_script(
            "arguments[0].click();",
            opcao,
        )

    wait_dom_stable(
        driver
    )

    log.info(
        "Cargo/Função selecionado: %s",
        cargo,
    )


def _salvar(
    driver,
    rotulo: str,
) -> None:
    """
    Salva UMA pessoa clicando exatamente no botão:
    #salvar-responsavel.

    Só retorna depois de o modal fechar e de o botão externo
    #criar-responsavel voltar a ficar disponível.
    """
    log.info(
        "%s | clicando em #salvar-responsavel...",
        rotulo,
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

    # Sem retry automático: é uma operação de gravação.
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
            f"{rotulo}: #salvar-responsavel foi clicado, "
            "mas o modal permaneceu aberto."
        ) from exc

    wait_dom_stable(
        driver
    )

    _wait(
        driver
    ).until(
        EC.element_to_be_clickable(
            BTN_CRIAR_RESPONSAVEL
        )
    )

    log.info(
        "%s | salvo; pronto para o próximo cadastro.",
        rotulo,
    )


def _cadastrar_um(
    driver,
    dados: DadosResponsavel,
) -> None:
    """
    Ciclo completo e isolado:
      criar -> preencher -> salvar -> esperar fechar.
    """
    if _cpf_ja_existe(
        driver,
        dados.cpf,
    ):
        log.warning(
            "%s | CPF %s já aparece na aba. Cadastro ignorado.",
            dados.rotulo,
            _formatar_cpf(
                dados.cpf
            ),
        )
        return

    _abrir_modal(
        driver,
        dados.rotulo,
    )

    _preencher_cpf_e_aguardar_nome(
        driver,
        dados.cpf,
        dados.rotulo,
    )

    if dados.email:
        log.info(
            "%s | preenchendo e-mail...",
            dados.rotulo,
        )

        _preencher(
            driver,
            EMAIL_RESPONSAVEL,
            dados.email,
        )

    _selecionar_cargo(
        driver,
        dados.cargo,
    )

    if dados.despacho:
        log.info(
            "%s | preenchendo despacho...",
            dados.rotulo,
        )

        _preencher(
            driver,
            DESPACHO_RESPONSAVEL,
            dados.despacho,
        )

    _salvar(
        driver,
        dados.rotulo,
    )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Ordem:
      1. abre aba 5;
      2. cadastra Responsável pela contratação direta;
      3. SALVA;
      4. clica novamente em Adicionar;
      5. cadastra Autoridade competente;
      6. SALVA.
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

    cadastros = _obter_cadastros(
        itens_processo
    )

    log.info(
        "▶ RESPONSÁVEIS | processo=%s | %d cadastro(s)",
        processo,
        len(
            cadastros
        ),
    )

    _abrir_aba_responsaveis(
        driver
    )

    for indice, dados in enumerate(
        cadastros,
        start=1,
    ):
        log.info(
            "Cadastro %d/%d | %s",
            indice,
            len(
                cadastros
            ),
            dados.rotulo,
        )

        _cadastrar_um(
            driver,
            dados,
        )

    log.info(
        "✓ Etapa Responsáveis concluída para o processo %s.",
        processo,
    )
