# selectors.py
"""
Centralização de seletores CSS do projeto ComprasNet (Step B – Aba Itens e DC)

Padrões:
- Somente CSS (evitar XPath; usar apenas se for inevitável).
- Funções utilitárias para seletores dinâmicos por card_id (p-card id='item-12345').
- Comentários didáticos para facilitar manutenção.
"""

# Texto-chave do item 21172 (usado em validações na tabela de catálogo)
TEXTO_SERVICO_21172 = "Treinamento Qualificação Profissional"


class S:
    # ========= ABA ITENS =========
    # Aba/entrada da seção "Itens"
    ITENS_ABA = "#collapse-1 > div > div.dropdown-item.ng-star-inserted.active > div > div.col-8.pl-5.pt-1 > a > div.pl-2"

    # Botão para abrir o catálogo (modal ou painel lateral) para adicionar item
    ADICIONAR_BTN = "#abrir-catalogo"

    # Campo de busca do catálogo (onde digitamos '21172')
    CODIGO_INPUT = "#palavra-pesquisa > div > input"

    # Botão para disparar a pesquisa
    LUPA_BTN = "#pesquisar-palavra"

    # ========= CATÁLOGO (TABELA RESULTADOS) =========
    # Tabela principal do catálogo – resultados do código pesquisado
    CATALOGO_TABELA = "#pn_id_119-table"

    # Célula de descrição dentro da tabela (para validar 'Treinamento Qualificação Profissional')
    CATALOGO_LINHA_DESCR = "#pn_id_119-table > tbody > tr > td.p-element.text-truncate"

    # Botão "Adicionar" (ícone de +) da linha correspondente na tabela
    CATALOGO_LINHA_BTN_ADICIONAR = "#pn_id_119-table > tbody > tr > td:nth-child(3) > button"

    # ========= MODAL (FLUXO ANTIGO / FALLBACK) =========
    # Em alguns fluxos antigos, após escolher o item, pode existir um botão "Adicionar item"
    SALVAR_ITEM_MODAL_BTN = "#adicionar-item"

    # ========= CARRINHO / DC =========
    # Ícone do carrinho (topo/direita)
    CARRINHO_BTN = "#ir-carrinho"

    # Botão "Adicionar itens no DC"
    DC_ADD_BTN = "#adicionar-itens"

    # Botão de confirmação (pode aparecer ou não)
    DC_CONFIRMAR_BTN = "#confirmar"

    # Fieldset onde ficam os cards da "Lista de Materiais e/ou Serviços Incluídos"
    DC_FIELDSET = "#area > div > div.mr-2.pt-2 > br-fieldset"

    # Tabela interna (quando renderiza como grid PrimeNG)
    DC_TABELA = "#pn_id_91-table"

    # ========= FUNÇÕES DINÂMICAS POR CARD =========
    # Os cards de item seguem o padrão <p-card id="item-1290410">...
    # Abaixo, funções que devolvem o CSS de campos/espelhos dentro do card a partir do ID numérico do card.

    @staticmethod
    def card_root(card_id: str) -> str:
        """Raiz do card (para buscas relativas, se necessário)."""
        return f"#item-{card_id}"

    @staticmethod
    def valor_input(card_id: str) -> str:
        """Input de valor estimado (unitário) do card."""
        return f"#valor-estimado-item-{card_id}"

    @staticmethod
    def valor_espelho(card_id: str) -> str:
        """Espelho do valor (label 'R$ X,0000') na área de detalhes do card."""
        return f"#detalhe-valor-unitario-item-{card_id}"

    @staticmethod
    def apelido_input(card_id: str) -> str:
        """Input do apelido (até 20 chars) do card."""
        return f"#apelido-item-{card_id}"

    @staticmethod
    def salvar_item(card_id: str) -> str:
        """Botão 'Salvar' do card."""
        return f"#salvar-item-{card_id}"

    # ========= CAMPOS ÚTEIS ADICIONAIS (se quiser validar/usar) =========
    @staticmethod
    def nome_item_label(card_id: str) -> str:
        """Span com o nome do serviço no topo do card (útil para sanity check)."""
        return f"#nome-item-{card_id}"

    @staticmethod
    def codigo_pdm_label(card_id: str) -> str:
        """Span com o código PDM do item (esperado: 21172)."""
        return f"#codigo-pdm-item-{card_id}"

    @staticmethod
    def quantidade_total_label(card_id: str) -> str:
        """Label que indica se a quantidade total está detalhada."""
        return f"#quantidade-total-item-{card_id}"

    @staticmethod
    def unidade_fornecimento_label(card_id: str) -> str:
        """Label de unidade de fornecimento (ex.: UNIDADE)."""
        return f"#fornecimento-item-{card_id}"

    @staticmethod
    def btn_expandir_card(card_id: str) -> str:
        """Botão/ícone para expandir/colapsar o card (quando necessário)."""
        return f"#btnExpandirItem{card_id}"

    # ========= FALLBACKS / EXTRAS =========
    # Em caso de mudanças de DOM, vale manter alguns seletores alternativos (comentados) para rápida troca.
    # Exemplo:
    # ALTERNATIVE_ITENS_ABA = "a[aria-controls='itens']"
    # ALTERNATIVE_CATALOGO_TABELA = "table.p-datatable-table"
