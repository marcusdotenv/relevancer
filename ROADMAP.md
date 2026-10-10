# Roadmap: POC robusta

Ordem por dependência: primeiro a stack sobe e tem teste, depois corrige a entrada, depois a leitura, depois o pipeline.

## Fase 0: Base reproduzível

- [x] Resolver `trie_pb2.py` (gerar no startup ou commitar).
- [x] Limpar `requirements.txt` e pinar imagens Docker.
- [x] Corrigir `.env.example`, tirar credenciais e bucket do código.
- [x] CI rodando os testes existentes.

**Pronto quando:** clone limpo + `docker compose up` funciona e o CI está verde.

## Fase 1: Validação de entrada

- [x] Limite de tamanho e charset do termo, na busca e no pipeline.
- [x] Normalizar case em ponto único (corrige `trie.py:44`).
- [x] `term` vazio retorna 422; `amount` com limites.
- [x] Prefixo com maiúscula encontra a partição no cache (`redis_trie_cache.py` usa `term[0]` sem lowercase).
- [x] Mesmo termo com case diferente soma a frequência em vez de a última inserção vencer (trie e merge do pipeline).
- [x] `Trie.search` faz lowercase como `insert` e `find_terms_by_prefix`.
- [x] Um teste para cada bug confirmado.

**Pronto quando:** busca com maiúscula, busca vazia e `amount` negativo estão corrigidos, e termo longo é rejeitado na entrada.

## Fase 2: Caminho de leitura

- [x] Redis guarda `prefixo → top-k` pré-computado, montado direto do arquivo de termos.
- [x] Cliente Redis async com pool único.
- [x] Fallback para cache vazio: busca responde 503 com `Retry-After` e dispara recarga a partir do arquivo de termos. Redis fora do ar também responde 503.
- [x] Benchmark antes/depois (`stress-test/`, resultados abaixo).
- [x] Guardar só os prefixos necessários: 29 mil em vez de 382 mil, Redis de 46 MB para 13 MB.
- [x] Remover `Trie`, `Node`, serializer protobuf, `trie.proto` e `generate_proto.sh`: não eram mais necessários.

**Pronto quando:** `GET /auto-complete` não desserializa nada e o p99 fica em poucos ms.

### Benchmark

Gatling, rampa de 1 a 20 usuários/s em 120 s, `api` com 1 CPU / 1 GB e `cache` com 0,5 CPU / 256 MB.

| Versão | Requests | Falhas | p50 | p99 | Vazão útil |
|---|---|---|---|---|---|
| Antes: trie protobuf desserializada por request | 8831 | 96,5% (timeout de 10 s) | 2557 ms | 8688 ms | 1,5 req/s |
| Depois: top-k por prefixo em hash do Redis | 8829 | 0% | 1 ms | 3 ms | 67 req/s (toda a carga) |
| Depois, só prefixos necessários | 8820 | 0% | 2 ms | 3 ms | 67 req/s (toda a carga) |

Antes, p50 e p99 são só das requests que não deram timeout. Depois, com rampa até 300 usuários/s em 60 s: 62571 requests, 0 falhas, média de 772 req/s, p50 22 ms, p95 3,1 s; a cauda degrada perto do pico. Com só os prefixos necessários, na mesma rampa: 62483 requests, 0 falhas, média de 801 req/s, p50 20 ms, p95 2,3 s.

## Fase 3: Pipeline confiável

- [ ] Idempotência: janela por timestamp do último run, não `[1d]` fixo.
- [ ] Lock contra execução simultânea.
- [ ] Rebuild fora do processo da API, com agendamento.
- [x] Troca atômica do cache (hash novo montado à parte e `RENAME` por cima do antigo).
- [ ] Erro do Loki propagado em vez de virar `[]`; tratar o limite de séries.

**Pronto quando:** rodar duas vezes seguidas não muda as frequências e toda falha aparece.

## Fase 4: Qualidade do sinal e segurança

- [x] Logar só o termo selecionado, não cada tecla (`POST /auto-complete/select`).
- [ ] Auth em `/pipeline` e rate limit em `/auto-complete`.
- [ ] Frequência mínima para um termo novo entrar nas sugestões.

**Pronto quando:** usuário anônimo não consegue inflar o ranking nem disparar o pipeline.

## Fase 5: Apresentação

- [ ] README com arquitetura, como rodar e números do benchmark.
- [ ] Suporte a acentos (normalização na busca).
- [ ] Tirar o JSON de 9,5 MB do git; corrigir typos.

## Fora do escopo

Fuzzy/typo, multi-idioma, escala horizontal.

## Decisões tomadas

- **Sinal de seleção.** `GET /auto-complete` não conta frequência. `POST /auto-complete/select` recebe o termo escolhido ou submetido (texto livre, validado) e é o único que entra no pipeline.
- **Case.** Termo é identificado em minúsculas; frequências de grafias diferentes somam. A grafia original é preservada e devolvida pela API. Quando duas grafias colidem, vale a primeira: a do arquivo de termos ganha da que vem dos logs.
- **Formato no Redis.** Hash `suggestions`: campo é o prefixo normalizado, valor é a lista JSON dos 50 termos mais buscados. Só é guardado o prefixo de uma letra ou aquele cujo prefixo anterior tem mais de 50 termos; os demais são achados filtrando a lista do prefixo guardado mais longo, lido com um `HMGET`. São 29 mil prefixos em 13 MB. Não existe mais árvore em código: o hash é a trie achatada, e o pipeline monta as listas direto do arquivo de termos (`build_suggestions_by_prefix`).
- **Empate de frequência.** Termo mais curto primeiro, depois ordem alfabética.
