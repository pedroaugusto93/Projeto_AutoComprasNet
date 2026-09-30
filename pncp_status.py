# pncp_status.py
"""
Controle simples de progresso do cadastro PNCP/ComprasNet.

Objetivos desta primeira versão:
  1. registrar na planilha o avanço do processo em PNCP_PERC_Conclusao;
  2. gravar o MESMO percentual em todas as linhas do mesmo PROCESSO;
  3. nunca reduzir um percentual já gravado;
  4. permitir que main.py ignore processos que já tenham qualquer percentual;
  5. concentrar os marcos em um único lugar para uma futura retomada por etapa.

IMPORTANTE:
Nesta versão, qualquer PNCP_PERC_Conclusao preenchido significa:
    "não executar automaticamente este processo".

No futuro, essa regra poderá ser trocada por:
    "ler o percentual e retomar da etapa seguinte".

Distribuição lógica:
  - dados_iniciais:     10%
  - dados_basicos:      +15% = 25%
  - dados_adicionais:   +15% = 40%
  - itens:              +25% = 65%
  - anexos:             +15% = 80%
  - responsaveis:       +10% = 90%
  - publicacao:         +10% = 100%

'localizar_processo' não recebe percentual porque é navegação/retomada,
não conteúdo cadastrado.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, List

import openpyxl

import config
from logger import get_logger
from models import ItemContratacao


log = get_logger(__name__)

COLUNA_PROCESSO = "PROCESSO"
COLUNA_PERCENTUAL = "PNCP_PERC_Conclusao"

# Aceita também nomes usados em versões/testes anteriores da planilha.
# A comparação dos títulos é case-insensitive por causa de _normalizar_titulo().
COLUNAS_PERCENTUAL_ACEITAS = (
    COLUNA_PERCENTUAL,
    "PNCP_PERC_concl",
    "PNCP_PERC_conclusao",
)

PESOS_ETAPAS = {
    "dados_iniciais": 10,
    "dados_basicos": 15,
    "dados_adicionais": 15,
    "itens": 25,
    "anexos": 15,
    "responsaveis": 10,
    "publicacao": 10,
}

MARCOS_ETAPAS = {
    "dados_iniciais": 10,
    "dados_basicos": 25,
    "dados_adicionais": 40,
    "itens": 65,
    "anexos": 80,
    "responsaveis": 90,
    "publicacao": 100,
}


def _normalizar_titulo(valor) -> str:
    return str(
        valor
        or ""
    ).strip().casefold()


def _coluna_por_titulo(
    ws,
    titulo: str,
    header_row: int = 1,
):
    alvo = _normalizar_titulo(
        titulo
    )

    for cell in ws[
        header_row
    ]:
        if _normalizar_titulo(
            cell.value
        ) == alvo:
            return cell.column

    return None


def _coluna_por_titulo_ou_cria(
    ws,
    titulo: str,
    header_row: int = 1,
):
    coluna = _coluna_por_titulo(
        ws,
        titulo,
        header_row,
    )

    if coluna is not None:
        return coluna

    nova = (
        ws.max_column
        or 0
    ) + 1

    ws.cell(
        row=header_row,
        column=nova,
        value=titulo,
    )

    log.warning(
        "Coluna %r não existia e foi criada na planilha.",
        titulo,
    )

    return nova


def _coluna_percentual_ou_cria(
    ws,
    header_row: int = 1,
):
    """
    Reaproveita a coluna de progresso já existente, inclusive aliases antigos.

    Evita criar uma segunda coluna quando a planilha já possui, por exemplo,
    PNCP_PERC_concl preenchida manualmente.
    """
    for titulo in COLUNAS_PERCENTUAL_ACEITAS:
        coluna = _coluna_por_titulo(
            ws,
            titulo,
            header_row,
        )

        if coluna is not None:
            return coluna

    return _coluna_por_titulo_ou_cria(
        ws,
        COLUNA_PERCENTUAL,
        header_row,
    )


def _percentual_numerico(
    valor,
):
    """
    Converte valores como:
      90%
      90
      90.0
      0.9  -> 90

    Retorna None quando vazio/inválido.
    """
    if valor is None:
        return None

    texto = str(
        valor
    ).strip()

    if not texto:
        return None

    tinha_percentual = "%" in texto

    texto = (
        texto
        .replace(
            "%",
            "",
        )
        .replace(
            ",",
            ".",
        )
        .strip()
    )

    try:
        numero = float(
            texto
        )
    except ValueError:
        return None

    if (
        not tinha_percentual
        and 0 <= numero <= 1
    ):
        numero *= 100

    return max(
        0,
        min(
            100,
            int(
                round(
                    numero
                )
            ),
        ),
    )


def _valor_percentual_item(
    item: ItemContratacao,
):
    """
    Obtém o progresso PNCP da linha, aceitando o cabeçalho atual e aliases.

    Cabeçalhos desconhecidos pelo modelo ficam em extras; por isso uma coluna
    antiga como PNCP_PERC_concl também precisa funcionar como trava.
    """
    for titulo in COLUNAS_PERCENTUAL_ACEITAS:
        valor = getattr(
            item,
            titulo,
            "",
        )

        if str(
            valor
            or ""
        ).strip():
            return valor

    extras = getattr(
        item,
        "extras",
        {},
    ) or {}

    titulos_aceitos = {
        _normalizar_titulo(
            titulo
        )
        for titulo in COLUNAS_PERCENTUAL_ACEITAS
    }

    for chave, valor in extras.items():
        if (
            _normalizar_titulo(
                chave
            ) in titulos_aceitos
            and str(
                valor
                or ""
            ).strip()
        ):
            return valor

    return ""


def valores_percentuais_grupo(
    itens_processo: Iterable[ItemContratacao],
) -> List[str]:
    """
    Retorna os valores não vazios encontrados no grupo, sem duplicar.
    """
    encontrados: List[str] = []

    for item in itens_processo:
        valor = str(
            _valor_percentual_item(
                item
            )
            or ""
        ).strip()

        if (
            valor
            and valor not in encontrados
        ):
            encontrados.append(
                valor
            )

    return encontrados


def grupo_ja_marcado(
    itens_processo: Iterable[ItemContratacao],
) -> bool:
    """
    Regra ATUAL de anti-duplicidade:
    qualquer percentual preenchido faz o processo ser ignorado.

    Esta função é o ponto que deverá mudar quando existir retomada
    inteligente por percentual.
    """
    return bool(
        valores_percentuais_grupo(
            itens_processo
        )
    )


def valores_percentuais_processo_planilha(
    processo: str,
) -> List[str]:
    """
    Lê a planilha diretamente e retorna os percentuais encontrados
    para o PROCESSO informado.

    Esta leitura é deliberadamente independente dos objetos já carregados
    em memória: funciona como segunda trava contra recadastro acidental.
    """
    caminho = Path(
        config.PLANILHA_PATH
    )

    wb = openpyxl.load_workbook(
        caminho,
        data_only=False,
        read_only=True,
    )

    try:
        ws = (
            wb[
                config.SHEET_NAME
            ]
            if config.SHEET_NAME in wb.sheetnames
            else wb.active
        )

        col_processo = _coluna_por_titulo(
            ws,
            COLUNA_PROCESSO,
        )

        if col_processo is None:
            raise RuntimeError(
                f"Coluna {COLUNA_PROCESSO!r} não encontrada na planilha."
            )

        colunas_percentual = []

        for titulo in COLUNAS_PERCENTUAL_ACEITAS:
            coluna = _coluna_por_titulo(
                ws,
                titulo,
            )

            if (
                coluna is not None
                and coluna not in colunas_percentual
            ):
                colunas_percentual.append(
                    coluna
                )

        if not colunas_percentual:
            return []

        alvo = str(
            processo
        ).strip()

        encontrados: List[str] = []

        for linha in range(
            2,
            ws.max_row + 1,
        ):
            valor_processo = str(
                ws.cell(
                    row=linha,
                    column=col_processo,
                ).value
                or ""
            ).strip()

            if valor_processo != alvo:
                continue

            for coluna in colunas_percentual:
                valor = str(
                    ws.cell(
                        row=linha,
                        column=coluna,
                    ).value
                    or ""
                ).strip()

                if (
                    valor
                    and valor not in encontrados
                ):
                    encontrados.append(
                        valor
                    )

        return encontrados

    finally:
        wb.close()


def percentual_atual_processo_planilha(
    processo: str,
) -> int | None:
    """
    Retorna o maior percentual numérico registrado para o processo.

    Uso atual:
      - 100% = processo totalmente concluído; não executar novamente;
      - 10% = marcador legado TEMPORÁRIO criado durante os testes de
        pré-cadastro e usado apenas para recuperar esses processos sem
        recriá-los.

    Nenhum percentual intermediário novo é gravado pelo fluxo atual.
    """
    valores = valores_percentuais_processo_planilha(
        processo
    )

    numericos = [
        numero
        for numero in (
            _percentual_numerico(
                valor
            )
            for valor in valores
        )
        if numero is not None
    ]

    return (
        max(
            numericos
        )
        if numericos
        else None
    )


def processo_ja_marcado_planilha(
    processo: str,
) -> bool:
    """
    Trava anti-duplicidade atual: somente 100% bloqueia o processo inteiro.
    """
    percentual = percentual_atual_processo_planilha(
        processo
    )

    return (
        percentual is not None
        and percentual >= 100
    )


def marco_da_etapa(
    etapa: str,
):
    return MARCOS_ETAPAS.get(
        etapa
    )


def registrar_etapa_concluida(
    processo: str,
    etapa: str,
    *,
    tentativas: int = 3,
    espera: float = 1.5,
) -> int | None:
    """
    Registra o marco da etapa para TODAS as linhas do mesmo processo.

    Nunca reduz percentual já existente.

    Se a planilha estiver aberta/bloqueada e não puder ser atualizada,
    levanta RuntimeError. Isso é intencional: a coluna é uma trava de
    segurança contra recadastro e não deve falhar silenciosamente.
    """
    percentual = marco_da_etapa(
        etapa
    )

    if percentual is None:
        return None

    caminho = Path(
        config.PLANILHA_PATH
    )

    ultimo_erro = None

    for tentativa in range(
        1,
        tentativas + 1,
    ):
        wb = None

        try:
            wb = openpyxl.load_workbook(
                caminho
            )

            ws = (
                wb[
                    config.SHEET_NAME
                ]
                if config.SHEET_NAME in wb.sheetnames
                else wb.active
            )

            col_processo = _coluna_por_titulo(
                ws,
                COLUNA_PROCESSO,
            )

            if col_processo is None:
                raise RuntimeError(
                    f"Coluna {COLUNA_PROCESSO!r} não encontrada na planilha."
                )

            col_perc = _coluna_percentual_ou_cria(
                ws
            )

            alvo = str(
                processo
            ).strip()

            linhas = []

            for linha in range(
                2,
                ws.max_row + 1,
            ):
                valor_processo = str(
                    ws.cell(
                        row=linha,
                        column=col_processo,
                    ).value
                    or ""
                ).strip()

                if valor_processo == alvo:
                    linhas.append(
                        linha
                    )

            if not linhas:
                raise RuntimeError(
                    f"Processo {processo!r} não encontrado na planilha."
                )

            for linha in linhas:
                celula = ws.cell(
                    row=linha,
                    column=col_perc,
                )

                atual = _percentual_numerico(
                    celula.value
                )

                novo = (
                    percentual
                    if atual is None
                    else max(
                        atual,
                        percentual,
                    )
                )

                celula.value = (
                    f"{novo}%"
                )

            wb.save(
                caminho
            )

            wb.close()
            wb = None

            log.info(
                "PNCP | processo=%s | etapa=%s | progresso=%d%% | %d linha(s) atualizada(s)",
                processo,
                etapa,
                percentual,
                len(
                    linhas
                ),
            )

            return percentual

        except PermissionError as exc:
            ultimo_erro = exc

            log.warning(
                "Planilha bloqueada ao registrar PNCP (%d/%d). "
                "Feche o Excel; nova tentativa em %.1fs...",
                tentativa,
                tentativas,
                espera,
            )

            if tentativa < tentativas:
                time.sleep(
                    espera
                )

        except Exception as exc:
            ultimo_erro = exc
            break

        finally:
            if wb is not None:
                try:
                    wb.close()
                except Exception:
                    pass

    raise RuntimeError(
        "Não foi possível gravar PNCP_PERC_Conclusao na planilha. "
        "O fluxo foi interrompido para evitar cadastrar etapas sem "
        "registrar o progresso."
    ) from ultimo_erro


def marcar_processo_concluido(
    processo: str,
) -> int:
    """
    Marca 100% somente depois que TODAS as etapas do processo terminarem.

    O controle percentual intermediário (10%, 25%, 40%...) está desativado
    nesta fase do projeto e poderá ser retomado futuramente.
    """
    resultado = registrar_etapa_concluida(
        processo,
        "publicacao",
    )

    if resultado != 100:
        raise RuntimeError(
            f"Falha ao marcar processo {processo!r} como 100%."
        )

    return resultado
