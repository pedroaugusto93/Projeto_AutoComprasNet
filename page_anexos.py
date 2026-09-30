# page_anexos.py
"""
Aba "4. Anexos" do ComprasNet.

Fluxo desta page:
  1. Abre "4. Anexos".
  2. Clica em "Anexar".
  3. Seleciona o tipo "Ato que autoriza a Contratação Direta".
  4. Lê o caminho do PDF na mesma coluna `file_path` usada pelo AutoSIGFIS.
  5. Anexa o arquivo diretamente no <input type="file"> oculto.

Importante:
Assim como no AutoSIGFIS, o Selenium NÃO automatiza a janela nativa de
seleção de arquivos do Windows. O caminho é enviado diretamente ao input
type="file", o que é mais estável e não depende de PyAutoGUI.
"""

from __future__ import annotations

import os
from typing import List

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import config
from logger import get_logger
from models import ItemContratacao
from utils_dom import wait_dom_stable


log = get_logger(__name__)
TIMEOUT = config.TIMEOUT


ABA_ANEXOS = (
    By.XPATH,
    "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
    "[.//span[normalize-space(.)='4. Anexos']]",
)

BTN_ANEXAR = (
    By.ID,
    "criar-anexo",
)

TIPO_ANEXO = (
    By.ID,
    "tipo-anexo",
)

OPCAO_ATO_AUTORIZA = (
    By.XPATH,
    "//li[@role='option' and ("
    "@aria-label='Ato que autoriza a Contratação Direta' "
    "or .//span[normalize-space(.)='Ato que autoriza a Contratação Direta']"
    ")]",
)

BTN_SELECIONAR_ARQUIVO = (
    By.ID,
    "bt_anexarPdf",
)


def _wait(driver, timeout: int | None = None) -> WebDriverWait:
    return WebDriverWait(
        driver,
        timeout or TIMEOUT,
    )


def _click(
    driver,
    locator,
    timeout: int | None = None,
):
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


def _processo_do_item(
    item: ItemContratacao,
) -> str:
    return str(
        getattr(
            item,
            "num_processo",
            None,
        )
        or getattr(
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


def _arquivo_do_item(
    item: ItemContratacao,
) -> str:
    """
    Usa a MESMA coluna do AutoSIGFIS: file_path.

    Mantém fallback para FILE_PATH em extras para tolerar planilhas antigas
    com o cabeçalho em maiúsculas.
    """
    valor = (
        getattr(
            item,
            "file_path",
            None,
        )
        or (
            getattr(
                item,
                "extras",
                {},
            )
            or {}
        ).get(
            "FILE_PATH",
            "",
        )
        or ""
    )

    return str(
        valor
    ).strip().strip('"').strip("'").strip()


def _obter_arquivo_processo(
    itens_processo: List[ItemContratacao],
) -> str:
    """
    Retorna o único file_path do processo.

    Como um processo pode ter várias linhas na planilha (um fornecedor/item
    por linha), caminhos repetidos são aceitos. Caminhos diferentes no mesmo
    processo são bloqueados para evitar anexar o documento errado.
    """
    arquivos = []

    for item in itens_processo:
        arquivo = _arquivo_do_item(
            item
        )

        if arquivo:
            arquivos.append(
                arquivo
            )

    unicos = []

    for arquivo in arquivos:
        chave = os.path.normcase(
            os.path.abspath(
                os.path.expandvars(
                    os.path.expanduser(
                        arquivo
                    )
                )
            )
        )

        if chave not in {
            os.path.normcase(
                os.path.abspath(
                    os.path.expandvars(
                        os.path.expanduser(
                            x
                        )
                    )
                )
            )
            for x in unicos
        }:
            unicos.append(
                arquivo
            )

    if not unicos:
        raise RuntimeError(
            "A coluna file_path está vazia para o processo atual. "
            "Não é possível anexar o ato autorizativo."
        )

    if len(
        unicos
    ) > 1:
        raise RuntimeError(
            "Há mais de um file_path diferente para o mesmo processo: "
            + " | ".join(
                unicos
            )
        )

    arquivo = os.path.abspath(
        os.path.expandvars(
            os.path.expanduser(
                unicos[0]
            )
        )
    )

    if not os.path.isfile(
        arquivo
    ):
        raise FileNotFoundError(
            f"Arquivo informado em file_path não encontrado: {arquivo}"
        )

    return arquivo


def _abrir_aba_anexos(
    driver,
) -> None:
    log.info(
        "Abrindo aba '4. Anexos'..."
    )

    _click(
        driver,
        ABA_ANEXOS,
    )

    wait_dom_stable(
        driver
    )

    _wait(
        driver
    ).until(
        EC.presence_of_element_located(
            BTN_ANEXAR
        )
    )

    log.info(
        "Aba '4. Anexos' aberta."
    )


def _abrir_novo_anexo(
    driver,
) -> None:
    log.info(
        "Clicando em 'Anexar'..."
    )

    _click(
        driver,
        BTN_ANEXAR,
    )

    wait_dom_stable(
        driver
    )

    _wait(
        driver
    ).until(
        EC.presence_of_element_located(
            TIPO_ANEXO
        )
    )

    log.info(
        "Formulário de anexo aberto."
    )


def _selecionar_tipo_anexo(
    driver,
) -> None:
    alvo = (
        "Ato que autoriza a Contratação Direta"
    )

    combo = _wait(
        driver
    ).until(
        EC.presence_of_element_located(
            TIPO_ANEXO
        )
    )

    atual = (
        combo.text
        or combo.get_attribute(
            "aria-label"
        )
        or ""
    ).strip()

    if atual == alvo:
        log.info(
            "Tipo de anexo já selecionado: %s",
            alvo,
        )
        return

    log.info(
        "Selecionando tipo de anexo: %s",
        alvo,
    )

    _click(
        driver,
        TIPO_ANEXO,
    )

    opcao = _wait(
        driver
    ).until(
        EC.visibility_of_element_located(
            OPCAO_ATO_AUTORIZA
        )
    )

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
            EC.presence_of_element_located(
                OPCAO_ATO_AUTORIZA
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            opcao,
        )

    wait_dom_stable(
        driver
    )

    def tipo_confirmado(d):
        try:
            el = d.find_element(
                *TIPO_ANEXO
            )

            texto = (
                el.text
                or el.get_attribute(
                    "aria-label"
                )
                or ""
            ).strip()

            return alvo in texto
        except StaleElementReferenceException:
            return False

    _wait(
        driver
    ).until(
        tipo_confirmado
    )

    log.info(
        "Tipo de anexo confirmado."
    )


def _localizar_input_file(
    driver,
):
    """
    Localiza o input[type=file] associado ao botão #bt_anexarPdf.

    Primeiro procura subindo a árvore a partir do botão. Se o componente
    PrimeNG/Angular deixar o input fora desse bloco, usa fallback global.
    """
    _wait(
        driver
    ).until(
        EC.presence_of_element_located(
            BTN_SELECIONAR_ARQUIVO
        )
    )

    input_file = driver.execute_script(
        """
        const btn = document.getElementById('bt_anexarPdf');

        if (btn) {
            let node = btn.parentElement;

            while (node) {
                const input = node.querySelector("input[type='file']");

                if (input) {
                    return input;
                }

                node = node.parentElement;
            }
        }

        return document.querySelector("input[type='file']");
        """
    )

    if input_file is None:
        raise RuntimeError(
            "O botão #bt_anexarPdf foi encontrado, mas nenhum "
            "<input type='file'> existe no DOM. "
            "Envie o outerHTML do bloco de upload para ajustarmos o seletor."
        )

    return input_file


def _anexar_arquivo(
    driver,
    arquivo: str,
) -> None:
    """
    Replica a estratégia do AutoSIGFIS: envia o caminho diretamente ao
    input[type=file], sem abrir/automatizar a janela nativa do Windows.
    """
    nome_arquivo = os.path.basename(
        arquivo
    )

    log.info(
        "Anexando arquivo: %s",
        nome_arquivo,
    )

    input_file = _localizar_input_file(
        driver
    )

    # Alguns componentes escondem completamente o input. Torná-lo visível
    # temporariamente evita ElementNotInteractable em versões do ChromeDriver.
    driver.execute_script(
        """
        const el = arguments[0];

        el.removeAttribute('hidden');
        el.removeAttribute('disabled');

        el.style.display = 'block';
        el.style.visibility = 'visible';
        el.style.opacity = '1';
        el.style.position = 'fixed';
        el.style.left = '0';
        el.style.bottom = '0';
        el.style.width = '1px';
        el.style.height = '1px';
        """,
        input_file,
    )

    input_file.send_keys(
        arquivo
    )

    def arquivo_confirmado(d):
        return bool(
            d.execute_script(
                """
                const nome = arguments[0].toLowerCase();

                return Array
                    .from(document.querySelectorAll("input[type='file']"))
                    .some(input => {
                        if (!input.files || input.files.length === 0) {
                            return false;
                        }

                        return Array
                            .from(input.files)
                            .some(file => (file.name || '').toLowerCase() === nome);
                    });
                """,
                nome_arquivo,
            )
        )

    try:
        _wait(
            driver
        ).until(
            arquivo_confirmado
        )
    except TimeoutException as exc:
        raise RuntimeError(
            "O caminho foi enviado ao input de arquivo, mas o navegador "
            "não confirmou o PDF selecionado."
        ) from exc

    wait_dom_stable(
        driver
    )

    log.info(
        "Arquivo selecionado no ComprasNet: %s",
        nome_arquivo,
    )


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Executa a etapa Anexos para UM ÚNICO processo.

    Esta versão para logo após selecionar o arquivo. Qualquer botão posterior
    de salvar/incluir será implementado quando o HTML dessa próxima ação for
    confirmado, evitando inventar seletor ou gravar algo indevido.
    """
    if not itens_processo:
        raise ValueError(
            "Nenhum item recebido em Anexos."
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

    if len(
        processos
    ) != 1:
        raise RuntimeError(
            "Anexos recebeu registros de mais de um processo: "
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

    arquivo = _obter_arquivo_processo(
        itens_processo
    )

    log.info(
        "▶ ANEXOS | processo=%s | arquivo=%s",
        processo,
        os.path.basename(
            arquivo
        ),
    )

    _abrir_aba_anexos(
        driver
    )

    _abrir_novo_anexo(
        driver
    )

    _selecionar_tipo_anexo(
        driver
    )

    _anexar_arquivo(
        driver,
        arquivo,
    )

    log.info(
        "✓ Etapa Anexos chegou até a seleção do arquivo para o processo %s.",
        processo,
    )
