# main.py
"""
ÚNICO ORQUESTRADOR do Projeto_AutoComprasNet.

Arquitetura:
  main.py
      -> decide o processo
      -> decide a ordem
      -> liga/desliga etapas
      -> passa para o próximo processo

As page_*.py executam somente sua própria responsabilidade.

Essa separação permite reaproveitar funcionalidades no futuro fluxo
de ATUALIZAÇÃO, especialmente page_localizar_processo.py.
"""

from __future__ import annotations

import time
from typing import Callable, Dict, List, Tuple

import config

import page_dados_adicionais
import page_dados_basicos
import page_dados_iniciais
import page_itens
import page_anexos
import page_responsaveis
import page_publicacao
import page_localizar_processo

from driver import get_driver
from helpers import carregar_itens
from logger import get_logger
from models import ItemContratacao


log = get_logger(__name__)


GrupoProcesso = Tuple[
    str,
    List[ItemContratacao],
]

Etapa = Tuple[
    str,
    Callable,
]


# =====================================================================
# CONFIGURAÇÃO DE EXECUÇÃO
# =====================================================================
#
# ALTERE SOMENTE ESTE BLOCO DURANTE OS TESTES.
#
# Estado atual de teste:
#   - contratação já existe;
#   - Dados Básicos, Dados Adicionais e Itens já estão preenchidos;
#   - localizar_processo abre a contratação existente em edição;
#   - queremos testar somente a nova etapa "5. Responsáveis".
#
ETAPAS_ATIVAS: Dict[str, bool] = {
    "dados_iniciais": False,
    "localizar_processo": True,
    "dados_basicos": False,
    "dados_adicionais": False,
    "itens": False,
    "anexos": False,
    "responsaveis": True,
    "publicacao": True,
}


# Durante o desenvolvimento:
# executa somente o primeiro processo da planilha.
PROCESSAR_APENAS_PRIMEIRO_PROCESSO = True


# =====================================================================
# AGRUPAMENTO POR PROCESSO
# =====================================================================

def _processo_do_item(
    item: ItemContratacao,
) -> str:
    return str(
        getattr(
            item,
            "processo",
            "",
        )
        or getattr(
            item,
            "PROCESSO",
            "",
        )
        or ""
    ).strip()


def agrupar_por_processo(
    itens: List[ItemContratacao],
) -> List[GrupoProcesso]:

    grupos: Dict[
        str,
        List[ItemContratacao],
    ] = {}

    ordem: List[str] = []

    for item in itens:
        processo = _processo_do_item(
            item
        )

        if not processo:
            raise RuntimeError(
                "Linha da planilha sem PROCESSO."
            )

        if processo not in grupos:
            grupos[
                processo
            ] = []

            ordem.append(
                processo
            )

        grupos[
            processo
        ].append(
            item
        )

    return [
        (
            processo,
            grupos[processo],
        )
        for processo in ordem
    ]


# =====================================================================
# ADAPTADORES DAS PAGES
# =====================================================================

def _etapa_dados_iniciais(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_dados_iniciais.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_localizar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_localizar_processo.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_dados_basicos(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_dados_basicos.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_dados_adicionais(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_dados_adicionais.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_itens(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_itens.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_anexos(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_anexos.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_responsaveis(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_responsaveis.executar_processo(
        driver,
        itens_processo,
    )


def _etapa_publicacao(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:

    page_publicacao.executar_processo(
        driver,
        itens_processo,
    )


# =====================================================================
# ORDEM OFICIAL DO CADASTRO
# =====================================================================
#
# Cadastro novo:
#
#   Dados Iniciais
#       ↓
#   Localizar Processo
#       ↓
#   Dados Básicos
#       ↓
#   Dados Adicionais
#       ↓
#   Itens
#       ↓
#   Anexos
#       ↓
#   Responsáveis
#       ↓
#   Publicação + recibo
#
FLUXO: List[Etapa] = [
    (
        "dados_iniciais",
        _etapa_dados_iniciais,
    ),
    (
        "localizar_processo",
        _etapa_localizar_processo,
    ),
    (
        "dados_basicos",
        _etapa_dados_basicos,
    ),
    (
        "dados_adicionais",
        _etapa_dados_adicionais,
    ),
    (
        "itens",
        _etapa_itens,
    ),
    (
        "anexos",
        _etapa_anexos,
    ),
    (
        "responsaveis",
        _etapa_responsaveis,
    ),
    (
        "publicacao",
        _etapa_publicacao,
    ),
]


# =====================================================================
# EXECUÇÃO DE UM PROCESSO
# =====================================================================

def executar_processo(
    driver,
    numero_processo: str,
    itens_processo: List[ItemContratacao],
) -> None:

    log.info(
        "=" * 72
    )

    log.info(
        "▶ PROCESSO: %s | %d registro(s)",
        numero_processo,
        len(
            itens_processo
        ),
    )

    log.info(
        "=" * 72
    )

    for nome_etapa, funcao in FLUXO:

        ativa = ETAPAS_ATIVAS.get(
            nome_etapa,
            False,
        )

        if not ativa:
            log.info(
                "⏭ ETAPA IGNORADA: %s",
                nome_etapa,
            )
            continue

        log.info(
            "▶ ETAPA: %s",
            nome_etapa,
        )

        inicio = time.time()

        funcao(
            driver,
            itens_processo,
        )

        log.info(
            "✓ ETAPA CONCLUÍDA: %s | %.1fs",
            nome_etapa,
            time.time() - inicio,
        )

    log.info(
        "✓ Fim das etapas ativas do processo %s.",
        numero_processo,
    )


# =====================================================================
# MAIN
# =====================================================================

def main() -> int:

    config.garantir_diretorios()

    inicio_total = time.time()

    driver = get_driver()

    driver.switch_to.window(
        driver.window_handles[0]
    )

    log.info(
        "Tela atual preservada."
    )

    log.info(
        "URL atual: %s",
        driver.current_url,
    )

    itens = carregar_itens()

    if not itens:
        log.error(
            "Planilha vazia."
        )
        return 1

    grupos = agrupar_por_processo(
        itens
    )

    log.info(
        "Processos encontrados: %d.",
        len(
            grupos
        ),
    )

    for processo, linhas in grupos:

        log.info(
            "  %s -> %d registro(s)",
            processo,
            len(
                linhas
            ),
        )

    etapas_ligadas = [
        nome
        for nome, _ in FLUXO
        if ETAPAS_ATIVAS.get(
            nome,
            False,
        )
    ]

    log.info(
        "Etapas ativas: %s",
        ", ".join(
            etapas_ligadas
        )
        if etapas_ligadas
        else "(nenhuma)",
    )

    if PROCESSAR_APENAS_PRIMEIRO_PROCESSO:

        grupos = grupos[:1]

        log.warning(
            "MODO TESTE: somente o primeiro processo será executado."
        )

    try:

        for indice, (
            processo,
            linhas,
        ) in enumerate(
            grupos,
            start=1,
        ):

            log.info(
                "Processo %d/%d",
                indice,
                len(
                    grupos
                ),
            )

            executar_processo(
                driver,
                processo,
                linhas,
            )

    except Exception:

        log.exception(
            "Falha na execução do fluxo."
        )

        log.info(
            "Tempo até a falha: %.1fs",
            time.time() - inicio_total,
        )

        return 1

    log.info(
        "=" * 72
    )

    log.info(
        "✓ EXECUÇÃO FINALIZADA | %.1fs",
        time.time() - inicio_total,
    )

    log.info(
        "=" * 72
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
