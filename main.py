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
import pncp_status

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
# FASE ATUAL:
#   - criar somente o cadastro inicial das contratações ainda não marcadas;
#   - NÃO localizar a contratação após a criação nesta execução;
#   - NÃO preencher as demais abas ainda;
#   - ao concluir dados_iniciais, registrar 10% como trava anti-duplicidade.
#
ETAPAS_ATIVAS: Dict[str, bool] = {
    # FASE ATUAL: somente o cadastro inicial da contratação.
    #
    # Depois que esta etapa conclui, o PNCP_PERC_Conclusao recebe 10%.
    # Como a regra atual ignora qualquer processo já marcado, uma nova
    # execução não recria a mesma contratação.
    "dados_iniciais": True,
    "localizar_processo": False,
    "dados_basicos": False,
    "dados_adicionais": False,
    "itens": False,
    "anexos": False,
    "responsaveis": False,
    "publicacao": False,
}


# Durante testes pontuais, altere para True para executar somente
# o primeiro processo pendente. Em operação normal, deixe False.
PROCESSAR_APENAS_PRIMEIRO_PROCESSO = False


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

    # Segunda trava de segurança: consulta o Excel imediatamente antes
    # de qualquer interação com o ComprasNet. Mesmo que o filtro do main
    # seja alterado/removido, processo já marcado não pode ser recadastrado.
    valores_perc_atuais = pncp_status.valores_percentuais_processo_planilha(
        numero_processo
    )

    if valores_perc_atuais:
        log.warning(
            "🛑 BLOQUEIO ANTI-DUPLICIDADE | %s | PNCP_PERC_Conclusao=%s | nenhuma etapa será executada",
            numero_processo,
            ", ".join(
                valores_perc_atuais
            ),
        )
        return

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

        percentual = pncp_status.registrar_etapa_concluida(
            numero_processo,
            nome_etapa,
        )

        if percentual is not None:
            log.info(
                "✓ PROGRESSO PNCP: %s -> %d%%",
                numero_processo,
                percentual,
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

    # =================================================================
    # PROCESSOS COM PNCP_PERC_Conclusao
    # =================================================================
    #
    # Regra temporária e conservadora:
    # qualquer percentual preenchido = NÃO executar automaticamente.
    #
    # No futuro, este ponto será substituído pela retomada inteligente
    # conforme o marco registrado.
    #
    grupos_pendentes = []

    for processo, linhas in grupos:

        # Consulta diretamente a planilha atual. Isso evita depender
        # somente dos objetos carregados em memória.
        valores_perc = pncp_status.valores_percentuais_processo_planilha(
            processo
        )

        if valores_perc:
            log.warning(
                "⏭ PROCESSO IGNORADO | %s | PNCP_PERC_Conclusao=%s",
                processo,
                ", ".join(
                    valores_perc
                ),
            )
            continue

        grupos_pendentes.append(
            (
                processo,
                linhas,
            )
        )

    grupos = grupos_pendentes

    log.info(
        "Processos pendentes após filtro PNCP: %d.",
        len(
            grupos
        ),
    )

    if not grupos:
        log.info(
            "Nenhum processo pendente para execução."
        )
        return 0

    if PROCESSAR_APENAS_PRIMEIRO_PROCESSO:

        grupos = grupos[:1]

        log.warning(
            "MODO TESTE: somente o primeiro processo será executado."
        )

    sucessos = 0
    falhas = 0

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

        try:
            executar_processo(
                driver,
                processo,
                linhas,
            )

            sucessos += 1

        except Exception:
            falhas += 1

            log.exception(
                "✗ PROCESSO COM FALHA | %s | seguindo para o próximo.",
                processo,
            )

            continue

    log.info(
        "=" * 72
    )

    log.info(
        "✓ EXECUÇÃO FINALIZADA | %.1fs | sucessos=%d | falhas=%d",
        time.time() - inicio_total,
        sucessos,
        falhas,
    )

    log.info(
        "=" * 72
    )

    return 1 if falhas else 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
