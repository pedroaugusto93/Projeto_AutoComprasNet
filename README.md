# Projeto AutoComprasNet

Automação da divulgação de **dispensas de licitação** no ComprasNet (SERPRO), via
Python + Selenium. Lê os dados de `cadastro.xlsx` e preenche o formulário de
contratação (Dados Básicos → Itens → DC → Documentos → Empenhos).

Mesma arquitetura do AutoSIGFIS: `config` centralizado, `page modules` por aba,
seletores centralizados, logging estruturado e modelo de dados tipado.

## Arquitetura

```
src/
├── config.py              # caminhos, timeouts, URL, dados de cabeçalho (1 ponto de verdade)
├── logger.py              # logging estruturado (console + arquivo rotativo)
├── models.py              # ItemContratacao (linha da planilha, tipada)
├── app_selectors.py       # seletores CSS centralizados (+ XPath isolado)
├── driver.py              # fábrica do WebDriver (conexão ao Chrome debug)
├── helpers.py             # leitura da planilha -> List[ItemContratacao]
├── utils_dom.py           # waits, clique/digitação, JS setter, evidências
├── page_dados_basicos.py  # aba Dados Básicos (pré-cadastro + localizar + dados)
├── page_itens.py          # aba Itens + envio ao DC
├── page_documentos.py     # aba Documentos (esqueleto)
├── page_empenhos.py       # aba Empenhos (esqueleto)
└── main.py                # orquestrador + relatório de execução
```

Fluxo de dependências (sem ciclos):
`main → page_* → {helpers, utils_dom, app_selectors, models} → {config, logger}`

## Pré-requisitos

1. Python 3.10+ e as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Chrome aberto em modo Remote Debugging (a autenticação é feita por você;
   a automação só se conecta à sessão já logada):
   ```bat
   "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
       --remote-debugging-port=9222 ^
       --user-data-dir="C:\chrome_debug"
   ```

## Execução

```bash
cd src
python main.py
```

## Configuração por ambiente (opcional)

Sem editar código, é possível sobrescrever via variáveis de ambiente:

| Variável               | Default                          |
|------------------------|----------------------------------|
| `COMPRASNET_PLANILHA`  | `src/cadastro.xlsx`              |
| `COMPRASNET_SHEET`     | `Sheet1`                         |
| `CHROME_DEBUG_HOST`    | `127.0.0.1`                      |
| `CHROME_DEBUG_PORT`    | `9222`                           |
| `TIMEOUT_SECONDS`      | `30`                             |
| `COMPRASNET_URL`       | URL de execução do ComprasNet    |
| `COMPRASNET_CODIGO_ITEM` | `21172`                        |

## Logs e evidências

- Log: `src/logs/comprasnet.log`
- Screenshots de evidência: `src/logs/shots/`

## Notas de manutenção

- **Fundamento Legal** está desativado em `page_dados_basicos._fundamento_legal()`:
  os seletores eram posicionais (`p-treenode:nth-child`) e frágeis. Reabilitar só
  após confirmar a estrutura atual da árvore.
- **Dados** vêm de `cadastro.xlsx` (a MESMA planilha do AutoSIGFIS — colunas
  do SuperFiltro). O modelo `ItemContratacao` espelha os cabeçalhos, então a
  mesma planilha serve aos dois projetos.
- **Constantes** (não variam por linha) ficam em `config.Constantes`:
  justificativa ("MPRJ não é órgão SISG"), modalidade (dispensa de licitação),
  fundamento legal, item=1, qtd=1, unidade.
- **Datas estimadas** ainda não têm coluna na planilha: usam `config.Provisorio`
  como fallback até virem do PNCP.
- **PNCP**: `ItemContratacao` tem uma seção reservada (data_inicio_estimada,
  data_fim_estimada, modo_disputa, moeda, srp). Basta criar a coluna na planilha
  com o mesmo nome que `from_row` preenche sozinho — colunas desconhecidas vão
  para `item.extras` sem quebrar nada.
```
