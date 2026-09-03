# Monitor de Apartamentos — Brasília

Verifica periodicamente novos anúncios de apartamentos no **Wimoveis**,
**DFimoveis** e **61imoveis**, de acordo com os filtros definidos em
`config.yaml`, e publica uma página com os anúncios em uma página do
GitHub Pages.

## Como funciona

1. Um workflow do GitHub Actions roda o scraper algumas vezes por dia
   (veja `.github/workflows/monitor.yml`, editável).
2. O scraper busca os anúncios em cada site, aplica os filtros do
   `config.yaml` e compara com `data/seen.json` (o que já foi visto antes).
3. Gera `docs/index.html` com os anúncios **novos** em destaque e o restante
   dos anúncios que batem com o filtro.
4. O workflow commita o `data/seen.json` e o `docs/index.html` atualizados
   de volta no repositório, e publica a pasta `docs/` no GitHub Pages.

## Configurando os filtros

Edite `config.yaml`: bairros, faixa de preço, número de quartos, área,
venda/aluguel, e quais sites checar. Não precisa mexer em código para isso.

## Colocando no ar (passo a passo)

1. Crie um repositório novo no GitHub e suba estes arquivos (`git init`,
   `git add .`, `git commit`, `git remote add origin ...`, `git push`).
2. Em **Settings → Actions → General → Workflow permissions**, marque
   **"Read and write permissions"** (o workflow precisa disso para commitar
   `data/seen.json` e `docs/index.html` de volta).
3. Em **Settings → Pages → Build and deployment → Source**, escolha
   **"GitHub Actions"**.
4. Vá na aba **Actions** do repositório e rode o workflow "Monitor de
   imóveis" manualmente uma vez (botão "Run workflow") para gerar a
   primeira versão da página e conferir se está tudo certo.
5. Depois disso ele roda sozinho nos horários definidos no cron do workflow.
   A URL da página fica em `https://<seu-usuario>.github.io/<repo>/`.

## Rodando localmente (para testar/ajustar antes de subir)

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium   # só necessário por causa do 61imoveis
python -m scraper.main
```

Depois abra `docs/index.html` no navegador para ver o resultado.

## Sobre a robustez dos scrapers

Sites de imóveis mudam de layout ocasionalmente, o que pode fazer um scraper
parar de encontrar anúncios. Os scrapers de `wimoveis` e `dfimoveis` usam
requisições HTTP simples (o HTML já vem pronto do servidor); o de
`61imoveis` usa um navegador headless (Playwright) porque esse site carrega
os anúncios via JavaScript depois que a página abre.

Se algum site parar de retornar resultados:
- Confira os logs da execução na aba **Actions** do GitHub — o scraper
  registra quantos anúncios brutos encontrou em cada site.
- O código de cada site fica isolado em `scraper/sites/<nome>.py`, então dá
  para ajustar um sem mexer nos outros.
- Os seletores usados hoje são heurísticos (procuram links de anúncio e
  sobem na árvore HTML até achar o bloco com preço) — é uma abordagem
  propositalmente tolerante a pequenas mudanças de layout, mas mudanças
  grandes no site podem exigir ajuste.

## Limitações conhecidas

- A paginação de `wimoveis`/`dfimoveis` usa o parâmetro `?pagina=N`, que é
  o padrão mais comum nesse tipo de site, mas pode precisar de ajuste.
- O scraping deve ser usado com moderação (poucas execuções por dia, como
  já está configurado) para não sobrecarregar os sites nem correr risco de
  bloqueio de IP.
- Este projeto é para uso pessoal. Verifique os Termos de Uso de cada site
  antes de usar de forma mais intensa.
