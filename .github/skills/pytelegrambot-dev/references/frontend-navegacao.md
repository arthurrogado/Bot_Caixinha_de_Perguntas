# Frontend, Navegação e UI/UX

Padrões de interface, navegação e fluxos de interação em bots Telegram com pyTelegramBotAPI.

## Princípios de UI/UX

1. **Editar, não enviar** — Preferir editar a mensagem atual (`try_edit_message_text`, `try_edit_message_caption`) com fallback para `send_message`
2. **Sempre oferecer saída** — Botão Cancelar/Voltar em todo fluxo multi-etapas
3. **Confirmação antes de ações destrutivas** — Deletar, persistir, alterar dados críticos
4. **Feedback explícito** — `answer_callback_query` + mensagem de sucesso/erro
5. **Estado temporário na memória** — Persistir só no "Salvar" final
6. **Retorno ao menu** — Após completar uma ação, re-renderizar o menu de origem

## Callbacks — Privados vs Globais

### Globais (`Classe__metodo__args`)

- Passam pelo `automatic_run` em `bot.py`
- Navegação entre telas/componentes
- Formato: `NomeComponente__metodo__arg1__arg2`

```python
markup = Markup.generate_inline([
    [['Ver detalhes', f'Produto__detalhar__{id}']],
    [['Voltar', 'MainMenu__start']],
])
```

### Privados (prefixo `_`)

- **Não** passam pelo `automatic_run`
- Consumidos por `once_callback_query_handler` dentro do componente
- Para diálogos internos: confirmação, seleção, navegação local

```python
# Callbacks privados comuns:
'_cancelar', '_sim', '_nao'
'_confirmar_excluir_{id}'
'_gen_prev', '_gen_next', '_gen_toggle__{idx}'
'_opt1', '_opt2'
```

## Edição de Mensagens — Padrões

### Texto

```python
# Editar mensagem existente com fallback para send_message
self.bot.try_edit_message_text(
    "Texto atualizado",
    call=self.call,
    reply_markup=markup,
    parse_mode="HTML"
)
```

### Mídia (caption)

```python
# Editar caption de foto/vídeo com fallback
self.bot.try_edit_message_caption(
    "Nova legenda",
    self.userid,
    self.call,
    reply_markup=markup
)
```

### Ordem de fallback

1. `edit_message_text` / `edit_message_caption` (tenta editar)
2. Se `MessageNotModified` ou `MessageToEditNotFound` → `send_message` / `edit_message_from_callback`

## Helpers de Cancelamento

```python
# ReplyKeyboard com botão CANCELAR (útil em wizards de texto)
Markup.cancelar_keyboard()

# InlineKeyboard com botão CANCELAR (callback_data='cancelar')
Markup.cancelar_inline()
```

### Cancelamento via texto em wizards

```python
def receber_input(self, message):
    if message.text and message.text.strip().lower() == '/cancel':
        self.bot.send_message(self.userid, "❌ Cancelado.")
        return
    # processar input...
```

## Handlers One-Shot

### `once_callback_query_handler`

Registra handler que dispara **uma vez** e se auto-remove:

```python
self.bot.once_callback_query_handler(
    self.userid,
    self.processar_opcao,
    lambda call: call.data in ['_opt1', '_opt2', '_cancelar']
)
```

### `register_next_step_or_callback_handler`

Espera **mensagem OU callback** — o que chegar primeiro cancela o outro:

```python
msg = self.bot.send_message(self.userid, "Digite ou clique:", reply_markup=markup)
self.bot.register_next_step_or_callback_handler(
    self.userid,
    self.processar,
    filter_fn=lambda call: call.data in ['_opt1', '_opt2']
)
```

## Wizards (Formulários Multi-Etapas)

Fluxo multi-step onde o bot solicita entradas (texto/arquivo), guia o usuário e persiste ao final.

### Estrutura básica

```python
class CriarItem(BaseComponent):
    def __init__(self, bot, userid, call=None):
        super().__init__(bot, userid, call)

    def start(self):
        """Etapa 1: pedir o nome"""
        msg = self.bot.send_message(self.userid, "Digite o nome do item:")
        self.bot.register_next_step_handler_by_chat_id(self.userid, self.receber_nome)

    def receber_nome(self, message):
        """Etapa 2: pedir preço"""
        if message.text and message.text.strip().lower() == '/cancel':
            self.cancel()
            return

        self.nome = message.text
        msg = self.bot.send_message(self.userid, "Agora digite o preço:")
        self.bot.register_next_step_handler_by_chat_id(self.userid, self.receber_preco)

    def receber_preco(self, message):
        """Etapa 3: confirmação"""
        if message.text and message.text.strip().lower() == '/cancel':
            self.cancel()
            return

        self.preco = message.text
        markup = Markup.generate_inline([
            [['✅ Confirmar', '_sim'], ['❌ Cancelar', '_nao']]
        ])
        self.bot.send_message(
            self.userid,
            f"Nome: {self.nome}\nPreço: {self.preco}\n\nConfirma?",
            reply_markup=markup
        )
        self.bot.once_callback_query_handler(
            self.userid,
            self.confirmar,
            lambda call: call.data in ['_sim', '_nao']
        )

    def confirmar(self, call):
        """Etapa final: persistir ou cancelar"""
        if call.data == '_nao':
            self.cancel()
            return

        # Persistir no banco
        Item().criar(self.nome, self.preco)
        self.bot.try_edit_message_text("✅ Item criado!", call=call)
        # Retornar ao menu de origem
        GerenciarItem(self.bot, self.userid).start()
```

### UX de cada etapa

1. Dizer o que enviar
2. Oferecer Cancelar (`/cancel` ou botão inline)
3. Validar input e re-promptar se inválido
4. Após todas etapas: resumo + confirmação Sim/Não
5. Após persistir: retornar ao menu pai

### Wizards com input de arquivo

```python
def pedir_arquivo(self):
    msg = self.bot.send_message(self.userid, "Envie a imagem:")
    self.bot.register_next_step_handler_by_chat_id(self.userid, self.receber_arquivo)

def receber_arquivo(self, message):
    if not message.photo and not message.document:
        self.bot.send_message(self.userid, "⚠️ Envie uma imagem válida.")
        self.pedir_arquivo()  # re-promptar
        return

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    # continuar...
```

## Picklist (Multi-Seleção com Paginação)

Padrão genérico para selecionar múltiplos itens de um catálogo grande.

### Quando usar

- Catálogo com muitos itens (gêneros, tags, categorias)
- Multi-seleção em que o usuário pode testar combinações
- Persistência apenas quando clicar "Salvar"

### Estado local

```python
pagina_atual: int = 0
page_size: int = 8
catalogo: list[str] = [...]     # todos os itens
selecionados: set[str] = set()  # seleção atual
```

### Render

```python
def render_picklist(self):
    start = self.pagina_atual * self.page_size
    end = start + self.page_size
    pagina = self.catalogo[start:end]

    botoes = []
    for i, item in enumerate(pagina):
        idx_global = start + i
        icone = "✅" if item in self.selecionados else "⬜"
        botoes.append([[f"{icone} {item}", f"_gen_toggle__{idx_global}"]])

    # Navegação
    nav = []
    if self.pagina_atual > 0:
        nav.append(['⬅️', '_gen_prev'])
    if end < len(self.catalogo):
        nav.append(['➡️', '_gen_next'])
    if nav:
        botoes.append(nav)

    # Ações
    botoes.append([
        ['💾 Salvar', '_gen_salvar'],
        ['🗑️ Limpar', '_gen_limpar'],
        ['↩️ Voltar', '_gen_voltar'],
    ])

    markup = Markup.generate_inline(botoes)
    self.bot.try_edit_message_text(
        f"Selecione ({len(self.selecionados)} selecionados):",
        call=self.call,
        reply_markup=markup
    )

    self.bot.once_callback_query_handler(
        self.userid,
        self.processar_picklist,
        lambda call: call.data.startswith('_gen_')
    )
```

### Processar ações

```python
def processar_picklist(self, call):
    self.call = call  # atualizar referência

    if call.data == '_gen_prev':
        self.pagina_atual -= 1
        self.render_picklist()

    elif call.data == '_gen_next':
        self.pagina_atual += 1
        self.render_picklist()

    elif call.data.startswith('_gen_toggle__'):
        idx = int(call.data.split('__')[1])
        item = self.catalogo[idx]
        if item in self.selecionados:
            self.selecionados.discard(item)
        else:
            self.selecionados.add(item)
        self.render_picklist()

    elif call.data == '_gen_limpar':
        self.selecionados.clear()
        self.render_picklist()

    elif call.data == '_gen_salvar':
        self.salvar()

    elif call.data == '_gen_voltar':
        self.cancel()
```

### Persistência no Salvar

```python
def salvar(self):
    # Reconciliar: limpar vínculos antigos + inserir novos
    MeuDAO().atualizar_vinculos(self.item_id, list(self.selecionados))
    self.bot.try_edit_message_text("✅ Salvo!", call=self.call)
    # Retornar ao menu pai
    GerenciarItem(self.bot, self.userid).start()
```

### Pontos de atenção

- **Concorrência**: último "Salvar" vence se dois usuários editarem
- **Catálogo vazio**: renderizar estado amigável ("Nenhum item cadastrado")
- **Itens com caracteres especiais**: usar índices no callback, não o texto

## Retorno ao Menu

**Regra**: após completar qualquer ação (criar, editar, excluir), sempre retornar à tela do menu de opções de origem.

```
1. Usuário clica opção no menu → "Alterar nome"
2. Bot pede input → "Digite o novo nome:"
3. Usuário envia valor
4. Bot mostra confirmação → Sim/Não
5. Após confirmar/cancelar → re-renderizar menu pai
```

Nunca deixar o usuário "solto". Chamar o método `start` (ou equivalente) do componente de gerenciamento/edição.

## Modularização de Componentes

### Quando dividir em múltiplos arquivos

- Feature com mais de ~200 linhas
- Wizards de criação separados do menu de gerenciamento
- Edição de campos individuais em arquivos próprios

### Padrão de organização

```
App/Components/
  MeuRecurso/
    GerenciarRecurso.py    # Menu principal + CRUD read/delete
    CriarRecurso.py        # Wizard de criação
    EditarRecurso.py        # Menu de edição com sub-campos
    Editar/
      EditarCampoX.py      # Edição de campo específico
```

### Callbacks com subpastas

```python
# Subpasta com _ no caminho:
'MeuRecurso_CriarRecurso__start'
# → App.Components.MeuRecurso.CriarRecurso.CriarRecurso.start()

'MeuRecurso_Editar_EditarCampoX__iniciar__42'
# → App.Components.MeuRecurso.Editar.EditarCampoX.EditarCampoX.iniciar(42)
```

### Boas práticas de modularização

1. Separar **gerenciamento** (menu/CRUD) de **criação** (wizards)
2. Um arquivo por wizard complexo
3. Edições de campos individuais em subpasta `Editar/`
4. Manter o componente principal "fino" — delegando para sub-componentes
5. `__init__` via convenção de nome (último `_segment` = nome da classe)
