# Padrões avançados e Inline Queries

## Inline Queries — Arquitetura

```
Usuário digita → Telegram envia InlineQuery → bot.py inline_handler
   → Rate limit check
   → Queries(bot, userid, query_text, chat_type).get_results(offset, limit)
   → bot.answer_inline_query(results, next_offset, cache_time, is_personal)
```

### Classe `Queries`

Localizada em `App/Components/Queries.py`. Responsável por despachar inline queries por **prefixo**.

```python
class Queries:
    def __init__(self, bot: TeleBot, userid, query, chat_type):
        self.deep_link_base = f"https://t.me/{bot.get_me().username}?start="
        self.limit = 10
        self.default_thumbnail = "https://i.imgur.com/mbFdfhs.png"

    def get_results(self, offset: int, limit: int = 10):
        pesquisas = {
            'o:':   self.pesquisar_items,     # prefix → handler
            'u: ':  self.pesquisar_usuarios,
            # adicionar novos prefixos aqui
        }
        self.results = self.resultados_nao_encontrados()
        for key in pesquisas:
            if key in self.query or key.strip() == self.query.strip():
                self.results = pesquisas[key](self.query)
                break
        return self.results[:self.limit]
```

### Adicionar uma nova inline query

1. Criar método na classe `Queries`:
```python
def pesquisar_clientes(self, query: str):
    query = query.split('cli:')[1].strip()
    clientes = Clientes().pesquisar(query, self.offset, self.limit)
    return [self.article_cliente(c) for c in clientes] or self.resultados_nao_encontrados("Nenhum cliente")
```

2. Registrar prefixo no dicionário `pesquisas`:
```python
'cli:': self.pesquisar_clientes,
```

3. O usuário digita `@seubot cli:João` → match por prefixo → executa o método.

### Convenções de prefixo

| Formato | Quando usar |
|---|---|
| `prefixo:` (sem espaço) | Query obrigatória: `o:naruto` |
| `prefixo: ` (com espaço) | Query opcional: `est: 2024 01` ou `est: ` (vazio = lista tudo) |

### Exemplo de tabela de prefixos (referência)

Monte uma tabela documentando todos os prefixos do seu bot:

| Prefixo | Descrição | Pessoal? | Cache |
|---|---|---|---|
| `o:` | Pesquisar itens por nome | Não | 180s |
| `of:` | Itens favoritos do usuário | Sim | 1s |
| `g:` | Itens por categoria/gênero | Não | 180s |
| `u:` | Pesquisar usuários (admin) | Sim | 1s |

### Proteção de prefixos admin

Prefixos que expõem dados sensíveis devem verificar permissão no início:

```python
def pesquisar_usuarios(self, query: str):
    if Usuarios().is_not_admin(self.userid):
        return self.resultados_nao_encontrados("Ops, não encontrado...")
    # continuar...
```

## Deep links a partir de Inline Results

**Problema**: Inline queries não podem abrir telas do bot diretamente.
**Solução**: Cada `InlineQueryResultArticle` envia um `InputTextMessageContent` com link Markdown apontando para o deep link do bot.

```python
def article_item(self, item):
    texto = f"📦 Veja o item '{item['nome']}'"
    deep_link = self.deep_link_base + 'Item__visualizar__' + str(item['id'])
    return InlineQueryResultArticle(
        id=item['id'],
        title=item['nome'],
        input_message_content=InputTextMessageContent(
            f"[{texto}]({deep_link})",   # link clicável
            parse_mode='Markdown'
        ),
        description=item.get('descricao', ''),
        thumbnail_url=item.get('thumbnail', self.default_thumbnail)
    )
```

Quando o usuário toca no link da mensagem, o Telegram abre o bot com `/start Item__visualizar__42`, e o `automatic_run` roteia normalmente.

### Formato do deep link payload

```
Classe__metodo__arg1__arg2
```

Idêntico ao `callback_data`. Isso é intencional: o mesmo `automatic_run` trata ambos.

## Paginação em Inline Queries

Telegram suporta paginação nativa via `offset` / `next_offset`:

```python
@bot.inline_handler(lambda query: True)
def inline_handler(query: InlineQuery):
    offset = int(query.offset) if query.offset else 0
    limit = 50

    db = Queries(bot, query.from_user.id, query.query, query.chat_type)
    results = db.get_results(offset, limit)

    # Só define next_offset se recebeu exatamente `limit` resultados
    next_offset = str(offset + limit) if len(results) == limit else ''

    bot.answer_inline_query(
        query.id,
        results,
        next_offset=next_offset,
        cache_time=cache_time,
        is_personal=is_personal,
    )
```

O Telegram chama `inline_handler` novamente com `offset = "50"`, `"100"` etc. quando o usuário rola os resultados.

### Parâmetros de cache

| `cache_time` | `is_personal` | Caso de uso |
|---|---|---|
| 180 | False | Buscas públicas (obras, itens) |
| 1 | True | Dados pessoais (favoritos, vouchers) |
| 1800 | False | Listas que mudam raramente (lançamentos) |
| 1 | True | Dados admin (episódios, gestão) |

## Callbacks em componentes – Padrões

### Callback privado (`_prefixo`)

Para diálogos internos de um componente que NÃO devem ser roteados pelo `automatic_run`:

```python
def confirmar_exclusao(self, id):
    markup = Markup.generate_inline([
        [['✅ Sim, excluir', f'_confirmar_excluir_{id}']],
        [['❌ Cancelar', '_cancelar']]
    ])
    self.bot.send_message(self.userid, "Tem certeza?", reply_markup=markup)

    # Registra handler local (de uso único)
    self.bot.once_callback_query_handler(
        self.userid,
        self.processar_exclusao,
        custom_filter=lambda call: call.data.startswith('_confirmar_excluir_') or call.data == '_cancelar'
    )

def processar_exclusao(self, call):
    if call.data == '_cancelar':
        self.cancel()
        return
    id_item = call.data.split('_confirmar_excluir_')[1]
    # executa exclusão...
```

### Callbacks públicos (`Classe__metodo__args`)

Para navegação entre telas. Roteados automaticamente pelo `automatic_run`:

```python
markup = Markup.generate_inline([
    [['Ver detalhes', f'Produto__detalhar__{produto_id}']],
    [['Voltar', 'MainMenu__start']],
])
```

### `startFrom` — execução imediata no construtor

Se um `CallbackQuery` e um `startFrom` são passados ao `BaseComponent`, o método é executado imediatamente via `__init__`. Útil para callbacks especiais (ex. `start_from_here`):

```python
# No handler de callback em bot.py:
options = {
    'start_from_here': lambda: MainMenu(bot, userid, call, MainMenu.start_from_here)
}
```

## Tratamento de erros em inline

```python
try:
    bot.answer_inline_query(query.id, results, ...)
except ApiTelegramException as e:
    if "query is too old" in e.description:
        pass  # query expirou (>10s), nada a fazer
    else:
        print(f"Erro inline: {e}")
except Exception as e:
    try:
        bot.answer_inline_query(query.id, [], cache_time=1,
            switch_pm_text="Erro ao processar.",
            switch_pm_parameter="erro")
    except Exception:
        pass
```

## switch_inline_query em botões

Botões em menus podem abrir inline queries diretamente:

```python
# Abre inline query no chat atual
['🔍 Pesquisar', 'switch_inline_query_current_chat=o: ']

# Abre inline query em outro chat (seletor de chat)
['➡️ Compartilhar', f'switch_inline_query=o: {id_item}']
```

O `Markup.generate_inline` detecta `=` no segundo elemento e cria o tipo de botão correto automaticamente.

### Atalhos comuns em menus

```python
# Menu principal com atalhos inline
markup = Markup.generate_inline([
    [['🔍 Pesquisar', 'switch_inline_query_current_chat=o: ']],
    [['⭐ Favoritos', 'switch_inline_query_current_chat=of: ']],
    [['📈 Em alta', 'switch_inline_query_current_chat=ea: ']],
    [['🆕 Lançamentos', 'switch_inline_query_current_chat=l: ']],
])
```

## Mensagem de texto com deep link embutido

O handler de mensagens pode detectar links para o próprio bot em texto comum:

```python
@bot.message_handler(func=lambda m: True)
def receber(msg):
    entities = msg.entities or []
    for entity in entities:
        if entity.type == "url":
            if f"t.me/{bot.get_me().username}?start=" in msg.text:
                automatic_run(msg.text.split("start=")[1], userid)
                return
        elif entity.type == "text_link":
            if f"t.me/{bot.get_me().username}?start=" in entity.url:
                automatic_run(entity.url.split("start=")[1], userid)
                return
```

Assim deep links funcionam mesmo sem o usuário clicar no botão /start — basta colar o link.

## Checklist para nova feature

1. [ ] Criar classe em `App/Components/` (ou subpasta com `_` no callback)
2. [ ] Herdar `BaseComponent`
3. [ ] Métodos públicos = telas navegáveis via callback
4. [ ] Callbacks locais com prefixo `_`
5. [ ] Markup via `Markup.generate_inline()`
6. [ ] Permissões via `self.permission.check_is_admin()` se necessário
7. [ ] Inline query: adicionar prefixo + método em `Queries.pesquisas`
8. [ ] Deep links: usar `deep_link_base + 'Classe__metodo__id'`
9. [ ] Testes manuais: callback, deep link, inline search, paginação
