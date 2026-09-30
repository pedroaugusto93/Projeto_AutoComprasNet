# page_itens.py
"""
Aba "3. Itens/Grupos" do ComprasNet.

Fluxo implementado nesta etapa:
  1. Abre a aba "3. Itens/Grupos".
  2. Clica em "Adicionar" (#abrir-catalogo).
  3. Pesquisa o serviço pelo config.CODIGO_ITEM.
  4. Para cada valor DO PROCESSO ATUAL:
       - clica no "+" da linha do serviço;
       - preenche #valor-unitario;
       - clica em #adicionar-item ("Salvar");
       - aguarda voltar à tabela e repete.
  5. Ao terminar:
       - clica em #ir-carrinho;
       - clica em #adicionar-itens;
       - confirma em #confirmar ("Sim").
  6. Na lista de itens incluídos:
       - adiciona Local de Entrega em lote;
       - define quantidade = 1 para cada item.
  7. Para cada item, individualmente:
       - abre "Resultado";
       - informa CPF/CNPJ do fornecedor correspondente;
       - informa o valor com 4 casas decimais;
       - informa quantidade = 1;
       - salva.
  8. Para aqui, antes da próxima aba.

Observação importante:
Não há retry automático envolvendo operações de gravação, para evitar duplicidade
de itens caso o ComprasNet salve uma operação e a resposta visual demore.
"""

from __future__ import annotations

from typing import List, Tuple

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
from utils_dom import cur4, wait_dom_stable

log = get_logger(__name__)
TIMEOUT = config.TIMEOUT

Bucket = Tuple[str, List[ItemContratacao]]

# -------------------------- Seletores reais -------------------------- #

ABA_ITENS_XPATH = (
    "//nav[@id='collapse-1']"
    "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
    "[.//span[normalize-space(.)='3. Itens/Grupos']]"
)

ABRIR_CATALOGO = (By.ID, "abrir-catalogo")

PESQUISA_INPUT = (
    By.CSS_SELECTOR,
    "input[placeholder='Digite aqui o material ou serviço a ser pesquisado']",
)

PESQUISAR_PALAVRA = (By.ID, "pesquisar-palavra")

TABELA_SERVICO = (By.CSS_SELECTOR, "p-table#tbServico")
LINHAS_SERVICO = (By.CSS_SELECTOR, "p-table#tbServico tbody tr")

VALOR_UNITARIO = (By.ID, "valor-unitario")
SALVAR_ITEM = (By.ID, "adicionar-item")

IR_CARRINHO = (By.ID, "ir-carrinho")
ADICIONAR_ITENS_DC = (By.ID, "adicionar-itens")
CONFIRMAR_SIM = (By.ID, "confirmar")

# Lista de itens já adicionados ao DC.
CARDS_ITENS = (By.CSS_SELECTOR, "p-card[id^='item-']")
MARCAR_TODOS_ITENS = (
    By.CSS_SELECTOR,
    "input[aria-labelledby='label-marcar-todos-itens']",
)
ADICIONAR_LOCAIS_ENTREGA = (
    By.XPATH,
    "//button[contains(normalize-space(.), 'Adicionar Locais de Entrega')]",
)
QUANTIDADES_LOCAL_EM_LOTE = (
    By.CSS_SELECTOR,
    "input[id^='quantidade-item-']",
)

# Modal/área de Resultado.
RESULTADO_FORNECEDOR = (By.ID, "id-fornecedor")
RESULTADO_VALOR = (By.ID, "valor")
RESULTADO_QUANTIDADE = (By.ID, "quantidade")


# -------------------------- Helpers Selenium -------------------------- #

def _wait(driver, timeout: int | None = None) -> WebDriverWait:
    return WebDriverWait(driver, timeout or TIMEOUT)


def _click(driver, locator, timeout: int | None = None):
    """Clique robusto, com scroll e fallback JavaScript."""
    w = _wait(driver, timeout)

    el = w.until(EC.presence_of_element_located(locator))

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        el,
    )

    try:
        el = w.until(EC.element_to_be_clickable(locator))
        el.click()
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        el = w.until(EC.presence_of_element_located(locator))
        driver.execute_script("arguments[0].click();", el)

    return el


def _click_element(driver, el):
    """Clique robusto em um WebElement já encontrado."""
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        el,
    )

    try:
        el.click()
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        driver.execute_script("arguments[0].click();", el)


def _elementos_visiveis(driver, locator):
    """Retorna somente elementos atualmente visíveis para o locator."""
    return [
        el
        for el in driver.find_elements(*locator)
        if el.is_displayed()
    ]


def _esperar_elementos_visiveis(driver, locator, timeout: int | None = None):
    """Aguarda existir pelo menos um elemento visível."""
    return _wait(driver, timeout).until(
        lambda d: _elementos_visiveis(d, locator) or False
    )


def _botao_visivel_por_id(driver, element_id: str, *, habilitado: bool = False):
    """
    IDs como 'salvar' se repetem em componentes Angular diferentes.
    Por isso escolhemos o botão que estiver realmente visível e, quando pedido,
    habilitado.
    """
    def localizar(d):
        for el in d.find_elements(By.ID, element_id):
            try:
                if not el.is_displayed():
                    continue
                if habilitado and not el.is_enabled():
                    continue
                return el
            except StaleElementReferenceException:
                continue
        return False

    return _wait(driver).until(localizar)


def _preencher_elemento(driver, elemento, valor: str) -> str:
    """
    Limpa, digita e dispara blur. Funciona bem com os inputs Angular/PrimeNG
    usados nesta tela.
    """
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        elemento,
    )
    elemento.click()
    elemento.send_keys(Keys.CONTROL, "a")
    elemento.send_keys(Keys.DELETE)
    elemento.send_keys(str(valor))
    elemento.send_keys(Keys.TAB)

    return (elemento.get_attribute("value") or "").strip()


def _preencher_locator(driver, locator, valor: str) -> str:
    """Preenche o primeiro elemento realmente visível do locator."""
    elementos = _esperar_elementos_visiveis(
        driver,
        locator,
        timeout=TIMEOUT,
    )
    return _preencher_elemento(
        driver,
        elementos[0],
        valor,
    )


def _somente_digitos(valor: str) -> str:
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


def _mascarar_documento(valor: str) -> str:
    digitos = _somente_digitos(valor)
    if len(digitos) <= 4:
        return digitos
    return "*" * (len(digitos) - 4) + digitos[-4:]


def _processo_do_item(item: ItemContratacao) -> str:
    """
    Aceita tanto 'num_processo' quanto 'processo', para manter compatibilidade
    com versões diferentes do model.
    """
    valor = (
        getattr(item, "num_processo", None)
        or getattr(item, "processo", None)
        or ""
    )
    return str(valor).strip()


def _valor_do_item(item: ItemContratacao) -> str:
    """
    Prioriza valor_unitario. Mantém fallback para 'valor' caso o model mude.
    """
    valor = (
        getattr(item, "valor_unitario", None)
        or getattr(item, "valor", None)
        or "0"
    )
    return cur4(valor)


def _fornecedor_doc(item: ItemContratacao) -> str:
    valor = (
        getattr(item, "fornecedor_doc", None)
        or getattr(item, "CNPJ_CPF_FORNECEDOR", None)
        or ""
    )
    valor = str(valor).strip()

    # CPF/CNPJ: preferimos somente os dígitos para não depender da máscara
    # existente na planilha.
    digitos = _somente_digitos(valor)
    return digitos or valor


def _fornecedor_nome(item: ItemContratacao) -> str:
    return str(
        getattr(item, "fornecedor_nome", None)
        or getattr(item, "NOME_FORNECEDOR", None)
        or ""
    ).strip()


# ====================== 1) ABRIR ABA ITENS ====================== #

def _abrir_aba_itens(driver) -> None:
    log.info("Abrindo aba '3. Itens/Grupos'...")

    w = _wait(driver)

    botao = w.until(
        EC.presence_of_element_located((By.XPATH, ABA_ITENS_XPATH))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        botao,
    )

    try:
        botao = w.until(
            EC.element_to_be_clickable((By.XPATH, ABA_ITENS_XPATH))
        )
        botao.click()
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        botao = w.until(
            EC.presence_of_element_located((By.XPATH, ABA_ITENS_XPATH))
        )
        driver.execute_script("arguments[0].click();", botao)

    wait_dom_stable(driver)

    # A confirmação mais útil é o botão "Adicionar" da tela de itens.
    w.until(EC.presence_of_element_located(ABRIR_CATALOGO))

    log.info("Aba '3. Itens/Grupos' aberta.")


def executar_processo(
    driver,
    itens_processo: List[ItemContratacao],
) -> None:
    """
    Executa Itens + DC para UM ÚNICO processo.

    Esta é a função que deverá ser usada pelo fluxo completo do main:
        processo atual
            -> Dados Básicos
            -> Itens
            -> demais etapas
            -> publicação
            -> comprovante/print
        só então o main chama o próximo processo.
    """
    if not itens_processo:
        raise ValueError("Nenhum item foi recebido para o processo atual.")

    processos = {
        _processo_do_item(item)
        for item in itens_processo
        if _processo_do_item(item)
    }

    if len(processos) != 1:
        raise RuntimeError(
            "executar_processo recebeu registros de mais de um processo: "
            + ", ".join(sorted(processos))
        )

    num_processo = next(iter(processos))
    bucket: Bucket = (num_processo, itens_processo)

    log.info(
        "▶ PROCESSO ATUAL: %s | %d registro(s)",
        num_processo,
        len(itens_processo),
    )

    # A page cuida apenas da própria tela; quem decide QUANDO executá-la
    # e QUAL processo executar é exclusivamente o main.py.
    _abrir_aba_itens(driver)

    # Pré-validação dos dados que serão usados em Resultado.
    _validar_dados_resultado(
        itens_processo,
    )

    # Suporte a retomada segura:
    # se os cards já estiverem na lista superior (caso atual de teste),
    # NÃO recadastra nem envia novamente ao DC.
    cards_existentes = _detectar_cards_existentes(
        driver,
        quantidade_esperada=len(itens_processo),
        timeout=min(TIMEOUT, 5),
    )

    if cards_existentes:
        if len(cards_existentes) != len(itens_processo):
            raise RuntimeError(
                "Já existem itens na tela, mas a quantidade não coincide com "
                f"o processo atual: tela={len(cards_existentes)} | "
                f"planilha={len(itens_processo)}. "
                "Não vou cadastrar novamente para evitar duplicidade."
            )

        log.info(
            "RETOMADA: %d item(ns) já estão na lista do DC. "
            "Cadastro e envio ao DC serão ignorados.",
            len(cards_existentes),
        )
    else:
        cadastrar_itens(
            driver,
            bucket,
        )

        enviar_itens_ao_dc(
            driver,
            bucket,
        )

    # Depois de estarem na tabela superior, cada card é associado à linha
    # correspondente da planilha pela ordem de criação.
    card_ids = _validar_cards_do_processo(
        driver,
        itens_processo,
    )

    # Estratégia escolhida: local de entrega em lote (mais eficiente).
    preencher_locais_entrega_em_lote(
        driver,
        card_ids,
    )

    # Resultado sempre individual: CPF/CNPJ + valor com 4 casas + qtd 1.
    preencher_resultados(
        driver,
        card_ids,
        itens_processo,
    )

    log.info(
        "✓ Itens, Local de Entrega e Resultado concluídos para o processo %s.",
        num_processo,
    )


# ====================== 2) ABRIR CATÁLOGO/PESQUISAR ====================== #

def _clicar_search(driver) -> None:
    """
    Clica diretamente no botão real de pesquisa do catálogo:

        <button id="pesquisar-palavra" ...>

    Usar o ID evita confundir esta lupa com outros ícones fa-search da página.
    """
    log.info("Clicando no botão 'Pesquisar palavra'...")
    _click(
        driver,
        PESQUISAR_PALAVRA,
        timeout=TIMEOUT,
    )
    log.info("Pesquisa acionada.")


def _abrir_catalogo_e_pesquisar(driver) -> None:
    log.info("Abrindo catálogo de material/serviço...")

    _click(driver, ABRIR_CATALOGO)
    wait_dom_stable(driver)

    campo = _wait(driver).until(
        EC.visibility_of_element_located(PESQUISA_INPUT)
    )

    termo = str(config.CODIGO_ITEM).strip()

    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(Keys.DELETE)
    campo.send_keys(termo)

    log.info("Pesquisando serviço pelo código/termo: %s", termo)

    _clicar_search(driver)
    wait_dom_stable(driver)

    _wait(driver).until(
        EC.visibility_of_element_located(TABELA_SERVICO)
    )

    _wait(driver).until(
        lambda d: len(d.find_elements(*LINHAS_SERVICO)) > 0
    )

    # Já valida se existe uma linha compatível antes de iniciar as gravações.
    _localizar_linha_servico(driver)

    log.info("Serviço localizado no catálogo.")


def _localizar_linha_servico(driver):
    """
    Localiza a linha do serviço.

    Prioridade:
      1. Código exato na primeira célula;
      2. código/termo contido no texto da linha;
      3. TEXTO_SERVICO_ITEM, se existir no config.
    """
    codigo = str(getattr(config, "CODIGO_ITEM", "") or "").strip()
    descricao = str(
        getattr(config, "TEXTO_SERVICO_ITEM", "") or ""
    ).strip().lower()

    linhas = _wait(driver).until(
        lambda d: d.find_elements(*LINHAS_SERVICO)
    )

    # 1) código exato na primeira célula
    if codigo:
        for linha in linhas:
            try:
                tds = linha.find_elements(By.CSS_SELECTOR, "td")
                primeiro = (tds[0].text or "").strip() if tds else ""
                if primeiro == codigo:
                    return linha
            except StaleElementReferenceException:
                break

    # Reobtém a lista se houve rerender.
    linhas = driver.find_elements(*LINHAS_SERVICO)

    # 2) código contido no texto completo
    if codigo:
        for linha in linhas:
            try:
                texto = " ".join((linha.text or "").split())
                if codigo in texto:
                    return linha
            except StaleElementReferenceException:
                break

    linhas = driver.find_elements(*LINHAS_SERVICO)

    # 3) descrição configurada
    if descricao:
        for linha in linhas:
            try:
                texto = " ".join((linha.text or "").lower().split())
                if descricao in texto:
                    return linha
            except StaleElementReferenceException:
                break

    raise RuntimeError(
        "O serviço pesquisado não foi encontrado em p-table#tbServico. "
        f"CODIGO_ITEM={codigo!r}"
    )


# ====================== 3) CADASTRAR VALORES ====================== #

def _clicar_plus_servico(driver) -> None:
    """
    Reobtém a linha a cada ciclo, porque o Angular pode recriar a tabela
    depois de salvar um item.
    """
    linha = _localizar_linha_servico(driver)

    try:
        botao = linha.find_element(
            By.XPATH,
            ".//button[.//i[contains(concat(' ', normalize-space(@class), ' '), ' fa-plus ')]]",
        )
    except Exception as exc:
        raise RuntimeError(
            "Linha do serviço encontrada, mas o botão '+' não foi localizado."
        ) from exc

    _click_element(driver, botao)

    _wait(driver).until(
        EC.visibility_of_element_located(VALOR_UNITARIO)
    )


def _preencher_valor_unitario(driver, valor_fmt: str) -> None:
    campo = _wait(driver).until(
        EC.visibility_of_element_located(VALOR_UNITARIO)
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        campo,
    )

    # Primeiro tenta pela digitação real, que costuma conversar melhor
    # com diretivas de currency mask.
    campo.click()
    campo.send_keys(Keys.CONTROL, "a")
    campo.send_keys(Keys.DELETE)
    campo.send_keys(valor_fmt)
    campo.send_keys(Keys.TAB)

    def campo_tem_valor(d):
        try:
            atual = d.find_element(*VALOR_UNITARIO)
            return bool((atual.get_attribute("value") or "").strip())
        except Exception:
            return False

    try:
        WebDriverWait(driver, min(TIMEOUT, 5)).until(campo_tem_valor)
    except TimeoutException:
        # Fallback: setter nativo + eventos Angular.
        campo = _wait(driver).until(
            EC.presence_of_element_located(VALOR_UNITARIO)
        )

        driver.execute_script(
            """
            const el = arguments[0];
            const valor = arguments[1];

            const setter =
                Object.getOwnPropertyDescriptor(
                    HTMLInputElement.prototype,
                    'value'
                ).set;

            setter.call(el, valor);

            el.dispatchEvent(new Event('input',  {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('blur',   {bubbles: true}));
            """,
            campo,
            valor_fmt,
        )

        _wait(driver).until(campo_tem_valor)

    valor_tela = (
        driver.find_element(*VALOR_UNITARIO).get_attribute("value")
        or ""
    ).strip()

    log.info(
        "Valor unitário preenchido: solicitado=%s | tela=%s",
        valor_fmt,
        valor_tela,
    )


def _salvar_item(driver) -> None:
    _click(driver, SALVAR_ITEM)

    # Não repetimos o clique automaticamente: salvar é operação de escrita.
    # Aguardamos a tela voltar para a tabela do catálogo.
    wait_dom_stable(driver)

    _wait(driver).until(
        EC.invisibility_of_element_located(VALOR_UNITARIO)
    )

    _wait(driver).until(
        EC.visibility_of_element_located(TABELA_SERVICO)
    )

    _wait(driver).until(
        lambda d: len(d.find_elements(*LINHAS_SERVICO)) > 0
    )


def cadastrar_itens(driver, bucket: Bucket) -> None:
    """
    Pesquisa o serviço uma única vez e reaproveita a mesma linha para todos
    os valores do processo.
    """
    num_processo, linhas = bucket

    if not linhas:
        log.warning(
            "Processo %s sem itens. Nada a cadastrar.",
            num_processo,
        )
        return

    log.info(
        "Cadastrando %d item(ns) do processo %s...",
        len(linhas),
        num_processo,
    )

    # O catálogo e a pesquisa são feitos uma única vez.
    _abrir_catalogo_e_pesquisar(driver)

    for idx, item in enumerate(linhas, start=1):
        valor_fmt = _valor_do_item(item)

        log.info(
            "Item %d/%d | processo=%s | valor=%s",
            idx,
            len(linhas),
            num_processo,
            valor_fmt,
        )

        # "+" do serviço
        _clicar_plus_servico(driver)

        # Valor
        _preencher_valor_unitario(
            driver,
            valor_fmt,
        )

        # Salvar -> volta para a mesma tabela
        _salvar_item(driver)

        log.info(
            "Item %d/%d salvo.",
            idx,
            len(linhas),
        )

    log.info(
        "Todos os %d item(ns) foram cadastrados no processo %s.",
        len(linhas),
        num_processo,
    )


# ====================== 4) CARRINHO / ADICIONAR AO DC ====================== #

def enviar_itens_ao_dc(driver, bucket: Bucket) -> None:
    """
    Depois de cadastrar todos os valores:
      carrinho -> Adicionar itens no DC -> Sim.

    Para exatamente aqui.
    """
    num_processo, linhas = bucket

    log.info(
        "Finalizando itens do processo %s: carrinho -> DC -> confirmar...",
        num_processo,
    )

    _click(driver, IR_CARRINHO)
    wait_dom_stable(driver)

    _click(driver, ADICIONAR_ITENS_DC)
    wait_dom_stable(driver)

    # Aqui o "Sim" é obrigatório segundo o fluxo informado.
    _click(driver, CONFIRMAR_SIM)

    # Como é uma gravação, apenas aguardamos o modal de confirmação desaparecer.
    try:
        _wait(driver).until(
            EC.invisibility_of_element_located(CONFIRMAR_SIM)
        )
    except TimeoutException:
        # Não refaz o clique para evitar duplicidade.
        log.warning(
            "O botão 'Sim' foi clicado, mas o desaparecimento do modal "
            "não foi confirmado dentro do tempo. O clique NÃO será repetido."
        )

    wait_dom_stable(driver)

    log.info(
        "Itens do processo %s adicionados ao DC. "
        "Execução da etapa de Itens encerrada aqui.",
        num_processo,
    )


# ====================== 5) LOCAL DE ENTREGA ====================== #

def _listar_cards_itens(driver):
    """
    Retorna os cards atuais em ordem de criação (ID numérico crescente).
    Os IDs reais seguem o padrão item-3442827, item-3442828, ...
    """
    cards = _esperar_elementos_visiveis(
        driver,
        CARDS_ITENS,
        timeout=TIMEOUT,
    )

    def chave(card):
        raw = (card.get_attribute("id") or "").replace("item-", "")
        try:
            return int(raw)
        except ValueError:
            return 10**18

    return sorted(cards, key=chave)


def _id_card(card) -> str:
    raw = card.get_attribute("id") or ""
    if not raw.startswith("item-"):
        raise RuntimeError(f"Card com ID inesperado: {raw!r}")
    return raw.split("item-", 1)[1]


def _detectar_cards_existentes(
    driver,
    quantidade_esperada: int,
    timeout: int = 5,
):
    """
    Aguarda a renderização dos cards já existentes.

    Se a tela já tiver itens, espera até que a quantidade esperada esteja
    renderizada. Isso evita interpretar uma renderização parcial (1, 2, 3...)
    como se fosse a lista definitiva.
    """
    ultimo_encontrado = []

    def localizar(d):
        nonlocal ultimo_encontrado

        cards = []
        for el in d.find_elements(*CARDS_ITENS):
            try:
                if el.is_displayed():
                    cards.append(el)
            except StaleElementReferenceException:
                continue

        ultimo_encontrado = cards

        if len(cards) >= quantidade_esperada:
            return cards

        return False

    try:
        return WebDriverWait(driver, timeout).until(localizar)
    except TimeoutException:
        # Se nenhum card apareceu, a contratação realmente pode estar vazia.
        if not ultimo_encontrado:
            return []

        # Se alguns apareceram, devolvemos para a trava de quantidade acusar
        # a inconsistência em vez de recadastrar por cima.
        return ultimo_encontrado


def _validar_cards_do_processo(
    driver,
    linhas: List[ItemContratacao],
) -> List[str]:
    """
    Faz uma trava de segurança antes de associar fornecedores.

    Cada linha da planilha precisa corresponder exatamente a um card da tela.
    Como os itens são criados na mesma ordem das linhas do processo, o item 1
    da tela recebe o fornecedor da primeira linha, o item 2 da segunda etc.
    """
    cards = _listar_cards_itens(driver)

    if len(cards) != len(linhas):
        raise RuntimeError(
            "Quantidade de cards na tela diferente da quantidade de registros "
            f"do processo: tela={len(cards)} | planilha={len(linhas)}. "
            "Execução interrompida para não associar fornecedor ao item errado."
        )

    card_ids: List[str] = []
    codigo_esperado = str(getattr(config, "CODIGO_ITEM", "") or "").strip()

    for idx, card in enumerate(cards, start=1):
        card_id = _id_card(card)
        card_ids.append(card_id)

        try:
            codigo_tela = (
                card.find_element(
                    By.CSS_SELECTOR,
                    f"#codigo-pdm-item-{card_id}",
                ).text
                or ""
            ).strip()
        except Exception:
            codigo_tela = ""

        if codigo_esperado and codigo_tela and codigo_tela != codigo_esperado:
            raise RuntimeError(
                f"Item {idx}: código da tela ({codigo_tela}) difere do "
                f"código esperado ({codigo_esperado})."
            )

    return card_ids


def _validar_dados_resultado(linhas: List[ItemContratacao]) -> None:
    """
    Valida todos os fornecedores antes de iniciar gravações de Resultado.
    Assim não descobrimos um CPF/CNPJ ausente depois de já salvar metade.
    """
    erros = []

    for idx, item in enumerate(linhas, start=1):
        doc = _fornecedor_doc(item)
        valor = _valor_do_item(item)

        if not doc:
            erros.append(f"item {idx}: CPF/CNPJ do fornecedor vazio")
        if not valor or valor == "0,0000":
            erros.append(f"item {idx}: valor vazio/zero")

    if erros:
        raise RuntimeError(
            "Dados insuficientes para preencher Resultado: "
            + "; ".join(erros)
        )


def _quantidade_total_card(driver, card_id: str) -> str:
    try:
        el = driver.find_element(
            By.ID,
            f"quantidade-total-item-{card_id}",
        )
        return " ".join((el.text or "").split()).lower()
    except Exception:
        return ""


def _local_entrega_pendente(driver, card_id: str) -> bool:
    texto = _quantidade_total_card(driver, card_id)
    texto_sem_acentos = (
        texto.replace("ã", "a")
        .replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
    )
    return (
        not texto
        or "nao detalhado" in texto_sem_acentos
        or "<nao detalhado>" in texto_sem_acentos
    )


def _marcar_checkbox_card(driver, card_id: str) -> None:
    card = _wait(driver).until(
        EC.presence_of_element_located((By.ID, f"item-{card_id}"))
    )

    checkbox = card.find_element(
        By.CSS_SELECTOR,
        "input[type='checkbox']",
    )

    if not checkbox.is_selected():
        _click_element(driver, checkbox)


def preencher_locais_entrega_em_lote(
    driver,
    card_ids: List[str],
) -> None:
    """
    Caminho escolhido: LOCAL DE ENTREGA EM LOTE.

    É mais eficiente que abrir item por item e produz o mesmo resultado:
    quantidade 1 para cada item. Se algum item já estiver detalhado, ele é
    preservado e somente os pendentes são marcados.
    """
    pendentes = [
        card_id
        for card_id in card_ids
        if _local_entrega_pendente(driver, card_id)
    ]

    if not pendentes:
        log.info(
            "Locais de entrega já detalhados para todos os itens; etapa ignorada."
        )
        return

    log.info(
        "Adicionando local de entrega em lote para %d item(ns)...",
        len(pendentes),
    )

    # Se todos precisam de local, usa o "Marcar todos" — menos cliques.
    # Se parte já foi preenchida manualmente, marca somente os pendentes para
    # não criar um segundo local de entrega nos itens já concluídos.
    if len(pendentes) == len(card_ids):
        marcar_todos = _wait(driver).until(
            EC.element_to_be_clickable(MARCAR_TODOS_ITENS)
        )
        if not marcar_todos.is_selected():
            _click_element(driver, marcar_todos)
    else:
        for card_id in pendentes:
            _marcar_checkbox_card(driver, card_id)

    _click(
        driver,
        ADICIONAR_LOCAIS_ENTREGA,
        timeout=TIMEOUT,
    )

    wait_dom_stable(driver)

    campos = _esperar_elementos_visiveis(
        driver,
        QUANTIDADES_LOCAL_EM_LOTE,
        timeout=TIMEOUT,
    )

    if len(campos) != len(pendentes):
        raise RuntimeError(
            "A tabela de Local de Entrega abriu com quantidade inesperada "
            f"de linhas: esperadas={len(pendentes)} | encontradas={len(campos)}."
        )

    for idx, campo in enumerate(campos, start=1):
        valor_tela = _preencher_elemento(
            driver,
            campo,
            "1",
        )
        log.info(
            "Local de entrega %d/%d -> quantidade=%s",
            idx,
            len(campos),
            valor_tela or "1",
        )

    # O id="salvar" é reutilizado em outros componentes; escolhemos o visível.
    salvar = _botao_visivel_por_id(
        driver,
        "salvar",
        habilitado=True,
    )
    _click_element(driver, salvar)

    # Não repetimos Salvar automaticamente.
    _wait(driver).until(
        lambda d: not _elementos_visiveis(
            d,
            QUANTIDADES_LOCAL_EM_LOTE,
        )
    )

    wait_dom_stable(driver)

    # Confirma visualmente que todos os pendentes deixaram de estar
    # "<não detalhado>".
    _wait(driver).until(
        lambda d: all(
            not _local_entrega_pendente(d, card_id)
            for card_id in pendentes
        )
    )

    log.info(
        "Local de entrega salvo com quantidade 1 para %d item(ns).",
        len(pendentes),
    )


# ====================== 6) RESULTADO / FORNECEDOR ====================== #

def _expandir_card_se_necessario(driver, card_id: str) -> None:
    painel_id = f"collapseItem-{card_id}"

    def painel_aberto(d):
        try:
            painel = d.find_element(By.ID, painel_id)
            return "show" in (painel.get_attribute("class") or "").split()
        except Exception:
            return False

    if painel_aberto(driver):
        return

    _click(
        driver,
        (By.ID, f"btnExpandirItem{card_id}"),
        timeout=TIMEOUT,
    )

    _wait(driver).until(painel_aberto)


def _abrir_tab_resultado(driver, card_id: str):
    """
    Abre diretamente a aba Resultado do item.

    Regra atual confirmada na tela do ComprasNet:
    depois que Local de Entrega foi salvo, a aba Resultado já fica clicável.
    Não é necessário reabrir Locais de Entrega nem inspecionar o atributo
    disabled do LI pai.

    Fluxo:
      1. expande o card, se necessário;
      2. localiza #tab-resultados-{card_id};
      3. clica diretamente;
      4. aguarda o painel carregar e o botão '+ Resultado' aparecer.
    """
    _expandir_card_se_necessario(
        driver,
        card_id,
    )

    resultado_locator = (
        By.ID,
        f"tab-resultados-{card_id}",
    )

    log.info(
        "Item %s: clicando diretamente na aba Resultado...",
        card_id,
    )

    # Espera somente o link existir/estar visível.
    tab = _wait(driver).until(
        EC.visibility_of_element_located(
            resultado_locator
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        tab,
    )

    # Não usamos o atributo disabled do LI pai.
    # A referência confiável é o próprio <a id='tab-resultados-...'>.
    try:
        tab.click()
    except (
        ElementClickInterceptedException,
        StaleElementReferenceException,
    ):
        tab = _wait(driver).until(
            EC.presence_of_element_located(
                resultado_locator
            )
        )
        driver.execute_script(
            "arguments[0].click();",
            tab,
        )

    painel_locator = (
        By.ID,
        f"tabpanel-resultados-{card_id}",
    )

    def painel_resultado_carregado(d):
        try:
            painel = d.find_element(*painel_locator)

            # O melhor sinal de que a aba realmente abriu é o componente
            # interno de Resultado ou o botão "+ Resultado".
            botoes = painel.find_elements(
                By.CSS_SELECTOR,
                "button#criar-resultado",
            )

            if botoes:
                return painel

            # Também aceita painel selecionado/visível quando já existe
            # algum resultado cadastrado e o botão não estiver presente.
            aria = (
                painel.get_attribute("aria-selected")
                or ""
            ).lower()

            if aria == "true" and painel.is_displayed():
                return painel

            return False

        except (
            StaleElementReferenceException,
            Exception,
        ):
            return False

    try:
        painel = _wait(driver).until(
            painel_resultado_carregado
        )
    except TimeoutException as exc:
        try:
            classes = (
                driver.find_element(*resultado_locator)
                .get_attribute("class")
                or ""
            )
        except Exception:
            classes = "(aba não encontrada)"

        raise RuntimeError(
            f"Item {card_id}: clique em Resultado foi executado, "
            f"mas o painel não carregou. classes={classes!r}"
        ) from exc

    log.info(
        "Item %s: aba Resultado aberta.",
        card_id,
    )

    return painel


def _resultado_ja_existe(
    painel,
    documento: str,
) -> bool:
    """
    Proteção para retomada parcial: se o CPF/CNPJ já aparecer no conteúdo do
    painel de Resultado, não cria outro resultado para o mesmo fornecedor.
    """
    digitos_doc = _somente_digitos(documento)

    if not digitos_doc:
        return False

    try:
        texto_painel = painel.text or ""
    except StaleElementReferenceException:
        return False

    digitos_painel = _somente_digitos(texto_painel)
    return digitos_doc in digitos_painel


def _preencher_resultado_item(
    driver,
    card_id: str,
    item: ItemContratacao,
    indice: int,
    total: int,
) -> None:
    documento = _fornecedor_doc(item)
    fornecedor = _fornecedor_nome(item)
    valor_fmt = _valor_do_item(item)  # SEMPRE 4 casas decimais.

    log.info(
        "Resultado %d/%d | card=%s | preparando fornecedor=%s | doc=%s | valor=%s",
        indice,
        total,
        card_id,
        fornecedor or "(sem nome)",
        _mascarar_documento(documento),
        valor_fmt,
    )

    painel = _abrir_tab_resultado(
        driver,
        card_id,
    )

    if _resultado_ja_existe(
        painel,
        documento,
    ):
        log.info(
            "Resultado %d/%d já contém o fornecedor %s; inclusão ignorada.",
            indice,
            total,
            fornecedor or _mascarar_documento(documento),
        )
        return

    try:
        botao_criar = painel.find_element(
            By.CSS_SELECTOR,
            "button#criar-resultado",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Item {indice}: botão '+ Resultado' não localizado."
        ) from exc

    _click_element(driver, botao_criar)

    # CPF/CNPJ.
    doc_tela = _preencher_locator(
        driver,
        RESULTADO_FORNECEDOR,
        documento,
    )

    # Valor: regra confirmada pelo usuário -> QUATRO casas decimais.
    valor_tela = _preencher_locator(
        driver,
        RESULTADO_VALOR,
        valor_fmt,
    )

    # Quantidade fixa.
    qtd_tela = _preencher_locator(
        driver,
        RESULTADO_QUANTIDADE,
        "1",
    )

    log.info(
        "Resultado %d/%d | fornecedor=%s | doc=%s | valor=%s | qtd=%s",
        indice,
        total,
        fornecedor or "(sem nome)",
        _mascarar_documento(doc_tela or documento),
        valor_tela or valor_fmt,
        qtd_tela or "1",
    )

    # O Salvar nasce disabled e só habilita depois que o formulário valida
    # o fornecedor/valor/quantidade.
    salvar = _botao_visivel_por_id(
        driver,
        "salvar",
        habilitado=True,
    )

    _click_element(driver, salvar)

    # Operação de escrita: não repetimos o clique.
    _wait(driver).until(
        lambda d: not _elementos_visiveis(
            d,
            RESULTADO_FORNECEDOR,
        )
    )

    wait_dom_stable(driver)

    log.info(
        "Resultado %d/%d salvo.",
        indice,
        total,
    )


def preencher_resultados(
    driver,
    card_ids: List[str],
    linhas: List[ItemContratacao],
) -> None:
    """
    Resultado é necessariamente individual porque cada item recebe o
    CPF/CNPJ e o valor do fornecedor correspondente à sua linha da planilha.
    """
    if len(card_ids) != len(linhas):
        raise RuntimeError(
            "Não é possível casar Resultado: quantidade de cards e linhas "
            "da planilha é diferente."
        )

    log.info(
        "Preenchendo Resultado individual de %d item(ns)...",
        len(linhas),
    )

    for indice, (card_id, item) in enumerate(
        zip(card_ids, linhas),
        start=1,
    ):
        _preencher_resultado_item(
            driver,
            card_id,
            item,
            indice,
            len(linhas),
        )

    log.info(
        "Resultados preenchidos para todos os itens do processo."
    )


# Nome antigo mantido para compatibilidade com qualquer chamada já existente.
def localizar_e_casar_no_dc(driver, bucket: Bucket) -> None:
    enviar_itens_ao_dc(driver, bucket)
