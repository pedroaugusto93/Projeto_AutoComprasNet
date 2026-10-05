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
# FLUXO ATUAL:
#   - cada PROCESSO deve ser concluído do início ao fim;
#   - somente depois disso o próximo processo pode começar;
#   - 100% na planilha = processo já concluído, portanto ignorar;
#   - 10% existente é apenas marcador legado dos pré-cadastros criados
#     acidentalmente nos testes e serve para retomar após dados_iniciais;
#   - não gravar percentuais intermediários nesta fase do projeto.
#
ETAPAS_ATIVAS: Dict[str, bool] = {
    "dados_iniciais": True,
    "localizar_processo": True,
    "dados_basicos": True,
    "dados_adicionais": True,
    "itens": True,
    "anexos": True,
    "responsaveis": True,
    "publicacao": True,
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

    percentual_atual = pncp_status.percentual_atual_processo_planilha(
        numero_processo
    )

    if (
        percentual_atual is not None
        and percentual_atual >= 100
    ):
        log.warning(
            "🛑 BLOQUEIO ANTI-DUPLICIDADE | %s | 100%% | nenhuma etapa será executada",
            numero_processo,
        )
        return

    # Recuperação temporária dos dois pré-cadastros gerados durante os testes.
    # 10% significa apenas: dados_iniciais já foi executado; NÃO recriar.
    recuperar_pre_cadastro = (
        percentual_atual == 10
    )

    if (
        percentual_atual is not None
        and 0 < percentual_atual < 100
        and not recuperar_pre_cadastro
    ):
        raise RuntimeError(
            "Percentual intermediário não suportado nesta fase: "
            f"{numero_processo} = {percentual_atual}%. "
            "Interrompido para evitar duplicidade."
        )

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

    if recuperar_pre_cadastro:
        log.warning(
            "↻ RECUPERAÇÃO DE PRÉ-CADASTRO | %s | 10%% legado | "
            "dados_iniciais será ignorado e o fluxo continuará em localizar_processo.",
            numero_processo,
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

        if (
            recuperar_pre_cadastro
            and nome_etapa == "dados_iniciais"
        ):
            log.warning(
                "⏭ ETAPA IGNORADA POR RECUPERAÇÃO: dados_iniciais"
            )
            continue

        log.info(
            "▶ ETAPA: %s",
            nome_etapa,
        )

        log.info(
            "URL antes da etapa %s: %s",
            nome_etapa,
            driver.current_url,
        )

        inicio = time.time()

        funcao(
            driver,
            itens_processo,
        )

        log.info(
            "URL depois da etapa %s: %s",
            nome_etapa,
            driver.current_url,
        )

        # IMPORTANTE:
        # Não registrar 10%, 25%, 40% etc. nesta fase do projeto.
        # O percentual só é atualizado para 100% depois que TODAS as
        # etapas concluírem com sucesso.
        log.info(
            "✓ ETAPA CONCLUÍDA: %s | %.1fs",
            nome_etapa,
            time.time() - inicio,
        )

    pncp_status.marcar_processo_concluido(
        numero_processo
    )

    log.info(
        "✓ PROCESSO CONCLUÍDO DO INÍCIO AO FIM | %s | PNCP_PERC_Conclusao=100%%",
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
    # Regra atual:
    #   100% -> processo completo: ignorar.
    #   10%  -> pré-cadastro legado dos testes: manter para recuperação.
    #   vazio -> fluxo completo desde dados_iniciais.
    #
    grupos_pendentes = []

    for processo, linhas in grupos:

        percentual = pncp_status.percentual_atual_processo_planilha(
            processo
        )

        if (
            percentual is not None
            and percentual >= 100
        ):
            log.warning(
                "⏭ PROCESSO IGNORADO | %s | PNCP_PERC_Conclusao=100%%",
                processo,
            )
            continue

        if percentual == 10:
            log.warning(
                "↻ PROCESSO EM RECUPERAÇÃO | %s | 10%% legado | "
                "retomará após dados_iniciais",
                processo,
            )

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
    nao_localizados = 0

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

        except page_localizar_processo.ContratacaoNaoLocalizada:
            nao_localizados += 1

            log.warning(
                "↪ NÃO LOCALIZADO | %s | tentando o próximo processo da planilha.",
                processo,
            )

            continue

        except Exception:
            log.exception(
                "✗ PROCESSO COM FALHA APÓS MATCH | %s | execução interrompida. "
                "O próximo processo NÃO será iniciado.",
                processo,
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
        "✓ VARREDURA FINALIZADA | %.1fs | concluídos=%d | não localizados=%d",
        time.time() - inicio_total,
        sucessos,
        nao_localizados,
    )

    log.info(
        "=" * 72
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
