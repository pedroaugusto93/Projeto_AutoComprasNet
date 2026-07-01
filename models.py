# models.py
"""
Modelo de domínio: uma linha da cadastro.xlsx (a MESMA planilha do AutoSIGFIS).

Os nomes dos campos espelham exatamente os cabeçalhos da planilha — assim a
mesma cadastro.xlsx alimenta tanto o AutoSIGFIS quanto o AutoComprasNet, sem
tradução de nomes. As propriedades de conveniência (titulo, processo, etc.)
dão acesso limpo aos campos que os page modules realmente usam.

Estrutura da planilha (32 colunas):
  • 1–21  : bloco SuperFiltro (colagem direta)
  • 22–32 : bloco exclusivo AutoSIGFIS
  • DATA_INICIO: data de início (usada no campo "Data de início")
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict


@dataclass(slots=True)
class ItemContratacao:
    # ----------------- BLOCO SUPERFILTRO (colunas 1–21) ------------------ #
    PROCESSO: str = ""
    VALOR: str = ""
    CNPJ_CPF_FORNECEDOR: str = ""
    NOME_FORNECEDOR: str = ""
    PRAZO_EXECUCAO: str = ""
    ANO_EMPENHO: str = ""
    DATA_EMPENHO: str = ""          # preenche a "Data de término" (#data-fim-contratacao)
    DATA_INICIO: str = ""           # NOVA coluna -> "Data de início" (#data-inicio-contratacao)
    NUM_EMPENHO: str = ""
    NOME_CURSO: str = ""
    OBJETO: str = ""
    item: str = ""
    autoridade_cpf: str = ""
    data_ato: str = ""
    ordenador: str = ""
    resp_cpf: str = ""
    resp_email: str = ""
    resp_despacho: str = ""
    autoridade_nome: str = ""
    autoridade_email: str = ""
    autoridade_despacho: str = ""
    file_path: str = ""

    # --------------- BLOCO EXCLUSIVO AUTOSIGFIS / CONTROLE --------------- #
    TIPOLOGIA_VALUE: str = ""
    ITEM_LOTE_VALUE: str = ""
    STATUS: str = ""                 # controle AutoSIGFIS
    PERC_CONCLUSAO: str = ""         # % de conclusão
    DISPENSA_SIGFIS: str = ""        # controle AutoSIGFIS
    # Campos que aparecem em variantes da planilha (mantidos por compatibilidade).
    FUNDAMENTO_VALUE: str = ""
    NUM_ITEM: str = ""
    QTD_ITEM: str = ""
    UNID_MEDIDA: str = ""
    VALOR_UNIT: str = ""
    ATO_DOCUMENTO: str = ""
    TIPO_DOCUMENTO: str = ""
    COD_UG_SIAFE: str = ""
    VALOR_EMPENHO: str = ""

    # ------------------------- SEÇÃO PNCP (reservada) -------------------- #
    # Ainda sem coluna na planilha. Quando o PNCP for integrado, criar as
    # colunas correspondentes e elas serão preenchidas automaticamente por
    # from_row (basta o cabeçalho bater com o nome do campo).
    data_inicio_estimada: str = ""   # data estimada de início (PNCP)
    data_fim_estimada: str = ""      # data estimada de término (PNCP)
    modo_disputa: str = ""           # ex.: "Não se aplica"
    moeda: str = ""                  # ex.: "Real"
    srp: str = ""                    # Sistema de Registro de Preços (S/N)

    # Colunas da planilha não mapeadas acima (preserva sem quebrar).
    extras: Dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------------------------------- #
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "ItemContratacao":
        """Constrói o item a partir de um dict (linha do DataFrame)."""
        conhecidos = {f.name for f in fields(cls) if f.name != "extras"}
        base = {k: str(v).strip() for k, v in row.items() if k in conhecidos}
        extras = {k: v for k, v in row.items() if k not in conhecidos}
        return cls(**base, extras=extras)

    # ------------------ PROPRIEDADES DE CONVENIÊNCIA --------------------- #
    @property
    def processo(self) -> str:
        return self.PROCESSO

    # Alias mantido para código que ainda usa num_processo.
    @property
    def num_processo(self) -> str:
        return self.PROCESSO

    @property
    def titulo(self) -> str:
        """Título da contratação = nome do curso."""
        return self.NOME_CURSO

    @property
    def objeto(self) -> str:
        return self.OBJETO

    @property
    def fornecedor_nome(self) -> str:
        return self.NOME_FORNECEDOR

    @property
    def fornecedor_doc(self) -> str:
        return self.CNPJ_CPF_FORNECEDOR

    @property
    def valor_unitario(self) -> str:
        """Valor unitário do item (VALOR_UNIT); cai para VALOR se vazio."""
        return self.VALOR_UNIT or self.VALOR

    @property
    def data_inicio(self) -> str:
        """Data de início da contratação (coluna DATA_INICIO)."""
        return self.DATA_INICIO

    @property
    def data_conclusao(self) -> str:
        """Data de término/conclusão — preenchida com DATA_EMPENHO (regra do MPRJ)."""
        return self.DATA_EMPENHO

    @property
    def apelido(self) -> str:
        """Apelido do item (até 20 chars), priorizando o nome do fornecedor."""
        nome = (self.NOME_FORNECEDOR or "").strip() or (self.item or "").strip()
        nome = nome or "SemApelido"
        return nome[:20].replace("  ", " ")
