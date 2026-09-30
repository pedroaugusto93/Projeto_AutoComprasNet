# models.py
"""
Modelo de domínio: uma linha da cadastro.xlsx.

Os nomes dos campos espelham os cabeçalhos da planilha.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict


@dataclass(slots=True)
class ItemContratacao:
    PROCESSO: str = ""
    VALOR: str = ""
    CNPJ_CPF_FORNECEDOR: str = ""
    NOME_FORNECEDOR: str = ""
    PRAZO_EXECUCAO: str = ""
    ANO_EMPENHO: str = ""
    DATA_EMPENHO: str = ""
    DATA_INICIO: str = ""
    NUM_EMPENHO: str = ""
    NOME_CURSO: str = ""
    OBJETO: str = ""

    # Aba "2. Dados adicionais da contratação"
    # Cabeçalho esperado no Excel: processoLink
    processoLink: str = ""

    item: str = ""
    autoridade_cpf: str = ""
    data_ato: str = ""
    ordenador: str = ""
    resp_cpf: str = ""
    resp_email: str = ""
    resp_cargo: str = ""
    resp_despacho: str = ""
    autoridade_nome: str = ""
    autoridade_email: str = ""
    autoridade_despacho: str = ""
    file_path: str = ""

    TIPOLOGIA_VALUE: str = ""
    ITEM_LOTE_VALUE: str = ""
    STATUS: str = ""
    PERC_CONCLUSAO: str = ""
    DISPENSA_SIGFIS: str = ""
    FUNDAMENTO_VALUE: str = ""
    NUM_ITEM: str = ""
    QTD_ITEM: str = ""
    UNID_MEDIDA: str = ""
    VALOR_UNIT: str = ""
    ATO_DOCUMENTO: str = ""
    TIPO_DOCUMENTO: str = ""
    COD_UG_SIAFE: str = ""
    VALOR_EMPENHO: str = ""

    data_inicio_estimada: str = ""
    data_fim_estimada: str = ""
    modo_disputa: str = ""
    moeda: str = ""
    srp: str = ""

    extras: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "ItemContratacao":
        conhecidos = {f.name for f in fields(cls) if f.name != "extras"}
        base = {
            k: str(v).strip()
            for k, v in row.items()
            if k in conhecidos
        }
        extras = {
            k: v
            for k, v in row.items()
            if k not in conhecidos
        }
        return cls(**base, extras=extras)

    @property
    def processo(self) -> str:
        return self.PROCESSO

    @property
    def num_processo(self) -> str:
        return self.PROCESSO

    @property
    def titulo(self) -> str:
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
        return self.VALOR_UNIT or self.VALOR

    @property
    def processo_link(self) -> str:
        return (self.processoLink or "").strip()

    @property
    def data_inicio(self) -> str:
        return self.DATA_INICIO

    @property
    def data_conclusao(self) -> str:
        return self.DATA_EMPENHO

    @property
    def apelido(self) -> str:
        nome = (self.NOME_FORNECEDOR or "").strip() or (self.item or "").strip()
        nome = nome or "SemApelido"
        return nome[:20].replace("  ", " ")
