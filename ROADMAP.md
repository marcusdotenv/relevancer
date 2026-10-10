# Roadmap: POC robusta

Ordem por dependência: primeiro a stack sobe e tem teste, depois corrige a entrada, depois a leitura, depois o pipeline.

## Fase 0: Base reproduzível

- [x] Resolver `trie_pb2.py` (gerar no startup ou commitar).
- [x] Limpar `requirements.txt` e pinar imagens Docker.
- [x] Corrigir `.env.example`, tirar credenciais e bucket do código.
- [x] CI rodando os testes existentes.

**Pronto quando:** clone limpo + `docker compose up` funciona e o CI está verde.

## Fase 1: Validação de entrada

- [ ] Limite de tamanho e charset do termo, na busca e no pipeline.
- [ ] Normalizar case em ponto único (corrige `trie.py:44`).
- [ ] `term` vazio retorna 422; `amount` com limites.
- [ ] Prefixo com maiúscula encontra a partição no cache (`redis_trie_cache.py` usa `term[0]` sem lowercase).
- [ ] Mesmo termo com case diferente soma a frequência em vez de a última inserção vencer (trie e merge do pipeline).
- [ ] `Trie.search` faz lowercase como `insert` e `find_terms_by_prefix`.
- [ ] Um teste para cada bug confirmado.

**Pronto quando:** busca com maiúscula, busca vazia e `amount` negativo estão corrigidos, e termo longo é rejeitado na entrada.

## Fase 2: Caminho de leitura

- [ ] Redis guarda `prefixo → top-k` pré-computado; a trie vira estrutura só de build.
- [ ] Cliente Redis async com pool único.
- [ ] Fallback para cache vazio (TODO em `main.py:24`).
- [ ] Benchmark antes/depois.

**Pronto quando:** `GET /auto-complete` não desserializa nada e o p99 fica em poucos ms.

## Fase 3: Pipeline confiável

- [ ] Idempotência: janela por timestamp do último run, não `[1d]` fixo.
- [ ] Lock contra execução simultânea.
- [ ] Rebuild fora do processo da API, com agendamento.
- [ ] Troca atômica do cache (chaves versionadas).
- [ ] Erro do Loki propagado em vez de virar `[]`; tratar o limite de séries.

**Pronto quando:** rodar duas vezes seguidas não muda as frequências e toda falha aparece.

## Fase 4: Qualidade do sinal e segurança

- [ ] Logar só o termo selecionado, não cada tecla.
- [ ] Auth em `/pipeline` e rate limit em `/auto-complete`.
- [ ] Frequência mínima para um termo novo entrar nas sugestões.

**Pronto quando:** usuário anônimo não consegue inflar o ranking nem disparar o pipeline.

## Fase 5: Apresentação

- [ ] README com arquitetura, como rodar e números do benchmark.
- [ ] Suporte a acentos (normalização na busca).
- [ ] Tirar o JSON de 9,5 MB do git; corrigir typos e o acesso a atributo privado no serializer.

## Fora do escopo

Fuzzy/typo, multi-idioma, escala horizontal.

## Decisões em aberto

1. **Formato no Redis (Fase 2).** Recomendado: top-k por prefixo. Elimina a desserialização por request e o limite de profundidade do protobuf. Custo: mais chaves, e precisa de um teto de comprimento de prefixo. Alternativa: manter o protobuf e cachear a trie em memória na API; muda menos, mas mantém o limite de profundidade.
2. **Sinal de seleção (Fase 4).** Recomendado: endpoint novo `POST /auto-complete/select`, chamado quando o usuário escolhe uma sugestão. Muda o contrato com o cliente.
