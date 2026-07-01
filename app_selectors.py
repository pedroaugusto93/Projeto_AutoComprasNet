# app_selectors.py
"""
Centralização de seletores CSS do projeto AutoComprasNet.

Escada de prioridade (do mais estável ao mais frágil):
  1. #id-semantico            -> #criar-contratacao, #salvar-contratacao
  2. [ptooltip="Texto"]       -> botões de ícone
  3. [aria-label="Texto"]     -> opções de dropdown (NÃO usar o pn_id volátil)
  4. classe do Design System + ancestral estável
  5. (último recurso) XPath por texto -> ver XPATHS

NUNCA ancorar em: _ngcontent-*, pn_id_NN, ou nth-child do "Copiar seletor".
"""

from __future__ import annotations

import config

TEXTO_SERVICO_ITEM = config.TEXTO_SERVICO_ITEM


class S:
    """Seletores CSS estáveis do fluxo."""

    # ===================== PRÉ-CADASTRO (modal "Criar") =================== #
    CRIAR_BTN = "#criar-contratacao"                    # id semântico
    TITULO_INPUT = "#titulo-contratacao"

    # Categoria (p-dropdown) — sempre "Serviços".
    # Gatilho por id semântico; opção por aria-label (o id vira pn_id_* volátil).
    # OBS: se a categoria tiver virado p-dropdown PrimeNG (como o PCA), o gatilho
    # pode ser outro — confirmar. A opção por aria-label é estável de qualquer forma.
    CATEGORIA_TRIGGER = "#categoria-contratacao"
    CATEGORIA_OPCAO_SERVICOS = "li[role='option'][aria-label='Serviços']"

    DATA_INICIO_INPUT = "#data-inicio-contratacao"      # corrigido (era data-data-inicio)
    DATA_FIM_INPUT = "#data-fim-contratacao"            # corrigido (era data-data-fim)
    DESCRICAO_TEXTAREA = "#descricao-contratacao"
    JUSTIFICATIVA_TEXTAREA = "#justificativa-contratacao"
    CONCLUIR_BTN = "#salvar-contratacao"                # fica 'disabled' até validar

    # ============================ PCA (ano) ============================== #
    # Plano de Contratações Anual — seleciona o plano do ano da contratação.
    PCA_COMBO = "#input-pca"                            # span[role=combobox] que abre

    # ==================== TAB "Contratações Minhas UASG" ================= #
    TAB_MINHAS_UASG = "#contratacoes-minhauasg"

    # ======================= GRID DE CONTRATAÇÕES ======================== #
    # Linhas e botão editar têm id estável (contratacao-#### / editar-contratacao-####).
    GRID_LINHAS = "tr[id^='contratacao-']"
    GRID_TITULO_CELULA = "td:nth-child(4)"             # coluna Título
    GRID_INICIO_CELULA = "td:nth-child(7)"             # coluna Início
    GRID_CONCLUSAO_CELULA = "td:nth-child(8)"          # coluna Conclusão
    # Ao casar a linha, clicamos no link da coluna "Contratação" (não no lápis).
    LINK_CONTRATACAO_CELULA = "td.link-contratacao"
    EDITAR_BTN_PREFIXO = "button[id^='editar-contratacao-']"  # (fallback, não usado)

    # =============== DADOS BÁSICOS (após "Editar contratação") =========== #
    PROCESSO_INPUT = "#processo-contratacao"

    # Tipo de contratação (p-dropdown) — sempre "Dispensa de licitação".
    # Gatilho por id semântico (padrão {campo}-contratacao); opção por aria-label.
    TIPO_TRIGGER = "#tipo-contratacao"
    # Modo de disputa (p-dropdown) — sempre "Não se aplica".
    MODO_DISPUTA_TRIGGER = "#modo-disputa-contratacao"

    # Fundamentação legal: lápis abre a árvore; salvar confirma.
    FUNDAMENTO_EDITAR_ICON = "#edicao-fundamento-contratacao em.fa-pencil-square-o, em.fa-pencil-square-o"
    SALVAR_FUNDAMENTO_BTN = "#salvar-fundamento"

    # ============================= ABA ITENS ============================= #
    ITENS_ABA = (
        "#collapse-1 > div > div.dropdown-item.ng-star-inserted.active "
        "> div > div.col-8.pl-5.pt-1 > a > div.pl-2"
    )
    ADICIONAR_BTN = "#abrir-catalogo"
    CODIGO_INPUT = "#palavra-pesquisa > div > input"
    LUPA_BTN = "#pesquisar-palavra"

    # Tabela do catálogo — ancorar pela classe do DS, não pelo pn_id volátil.
    CATALOGO_TABELA = "p-table table, table.p-datatable-table"
    CATALOGO_LINHA_DESCR = "td.p-element.text-truncate"
    CATALOGO_LINHA_BTN_ADICIONAR = "td:nth-child(3) > button"

    SALVAR_ITEM_MODAL_BTN = "#adicionar-item"

    # ============================ CARRINHO / DC ========================== #
    CARRINHO_BTN = "#ir-carrinho"
    DC_ADD_BTN = "#adicionar-itens"
    DC_CONFIRMAR_BTN = "#confirmar"
    DC_FIELDSET = "#area > div > div.mr-2.pt-2 > br-fieldset"

    # ================= FUNÇÕES DINÂMICAS (por valor/id) ================== #
    @staticmethod
    def opcao_por_label(label: str) -> str:
        """Opção de p-dropdown por aria-label exato (ex.: 'Dispensa de licitação')."""
        return f"li[role='option'][aria-label='{label}']"

    @staticmethod
    def pca_opcao(label: str) -> str:
        """Opção do PCA por aria-label exato (ex.: 'PCA 2026 - Em Execução')."""
        return f"li[role='option'][aria-label='{label}']"

    @staticmethod
    def tree_no(aria_label: str) -> str:
        """Nó da árvore de fundamentos por aria-label exato (ex.: 'Art. 75')."""
        return f"li[role='treeitem'][aria-label='{aria_label}']"

    @staticmethod
    def tree_no_prefixo(prefixo: str) -> str:
        """Nó da árvore por início do aria-label (ex.: 'Inciso II:')."""
        return f"li[role='treeitem'][aria-label^='{prefixo}']"

    @staticmethod
    def card_root(card_id: str) -> str:
        return f"#item-{card_id}"

    @staticmethod
    def valor_input(card_id: str) -> str:
        return f"#valor-estimado-item-{card_id}"

    @staticmethod
    def valor_espelho(card_id: str) -> str:
        return f"#detalhe-valor-unitario-item-{card_id}"

    @staticmethod
    def apelido_input(card_id: str) -> str:
        return f"#apelido-item-{card_id}"

    @staticmethod
    def salvar_item(card_id: str) -> str:
        return f"#salvar-item-{card_id}"

    @staticmethod
    def nome_item_label(card_id: str) -> str:
        return f"#nome-item-{card_id}"

    @staticmethod
    def codigo_pdm_label(card_id: str) -> str:
        return f"#codigo-pdm-item-{card_id}"


class XPATHS:
    """XPath isolado — só onde o CSS não alcança (match por texto exato)."""

    @staticmethod
    def linha_por_titulo(titulo: str) -> str:
        return f"//tr[starts-with(@id,'contratacao-')][td[normalize-space(.)='{titulo}']]"

    @staticmethod
    def opcao_por_texto(texto: str) -> str:
        return f"//li[@role='option'][contains(normalize-space(.),'{texto}')]"

    @staticmethod
    def botao_por_texto(texto: str) -> str:
        """Botão por texto exato (ex.: 'Editar contratação')."""
        return f"//button[normalize-space(.)='{texto}']"
