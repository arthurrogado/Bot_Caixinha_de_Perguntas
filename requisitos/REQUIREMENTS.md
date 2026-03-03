# Caixinha de Perguntas — Requisitos

## Dependências Python

### Obrigatórias

| Pacote              | Versão Mínima | Uso                                  |
|---------------------|---------------|--------------------------------------|
| `pyTelegramBotAPI`  | ≥ 4.14.0     | Framework principal do bot Telegram  |
| `Pillow`            | ≥ 10.0.0     | Geração de imagens (cartões/stories) |

### Opcionais

| Pacote                    | Versão Mínima | Uso                                    |
|---------------------------|---------------|----------------------------------------|
| `mysql-connector-python`  | ≥ 8.0.0      | Backend MariaDB/MySQL (se DB_BACKEND="mariadb") |
| `Pyrogram`                | ≥ 2.0.0      | Bot secundário para operações pesadas   |
| `TgCrypto`                | ≥ 1.2.0      | Aceleração criptográfica para Pyrogram  |

## Instalação

```bash
# Obrigatórias
pip install pyTelegramBotAPI Pillow

# Opcional: MariaDB
pip install mysql-connector-python

# Opcional: Pyrogram
pip install Pyrogram TgCrypto
```

## Configuração

### 1. Criar `App/Config/secrets.py`

```python
BOT_TOKEN = "SEU_TOKEN_AQUI"
ADMINS_IDS = [123456789]       # Telegram user IDs dos admins
CLOUD_ID = -1001234567890      # Chat ID para backups (opcional)

# Opcional: Pyrogram
# API_ID = 12345
# API_HASH = "abc123"
# ADMIN_BOT_TOKEN = "TOKEN_PYROGRAM"
```

### 2. Configurar `App/Config/config.py`

- `DB_BACKEND`: `"sqlite"` (padrão) ou `"mariadb"`
- `DB_NAME`: nome do arquivo SQLite (padrão: `database.db`)
- `MARIADB_*`: configurações MariaDB (se usar)

## Requisitos do Sistema

- Python ≥ 3.10
- SQLite ≥ 3.35 (incluído no Python)
- MariaDB ≥ 10.5 (opcional)

## Requisitos Funcionais

### RF01 — Criar Caixinha de Perguntas
- Usuário informa título (máx. 80 caracteres)
- **Confirmação do título** antes de salvar (botões: Confirmar / Editar / Cancelar)
- Sistema gera cartão PNG (header gradiente) e deep link `cx-<uid>`
- Imagem enviada via `send_photo`

### RF02 — Responder Caixinha (Enviar Pergunta)
- Via deep link, inline query ou UUID manual
- Opção de envio anônimo
- Limite de 180 caracteres por pergunta
- Confirmação antes do envio (Sim / Editar / Cancelar)
- Suporte a `/cancel` para abortar o fluxo
- **Se o dono clicar no próprio link**, é redirecionado para gestão da caixinha
- Notifica dono da caixinha com cartão de imagem (HTML)
- **Silenciamento**: se caixinha está silenciada, notificação não é enviada

### RF03 — Minhas Caixinhas (via Inline Query)
- Acesso pelo menu principal via `switch_inline_query_current_chat`
- Prefixo de query: `mc <termo>` (ativas), `mc:c <termo>` (concluídas)
- Artigos inline mostram **data de criação** (não ID)
- Clicar no resultado envia deep link → bot abre **visão de gerenciamento**
- Botões curtos para evitar BUTTON_DATA_INVALID (≤ 64 bytes)

### RF04 — Gerenciar Caixinha
- Visão de gerenciamento (`ver`): cartão de imagem + botões inline
- Ações: **Concluir/Reativar** (`c`/`r`), **Silenciar/Ativar notificações** (`s`)
- Ver perguntas via `switch_inline_query_current_chat`: `p:<uid> `
- Cartão enviado via `send_photo`

### RF05 — Visualizar Perguntas (via Inline Query)
- Prefixo de query: `p:<uid> <termo>`
- Mostra **todas** as perguntas (respondidas e não respondidas)
- Clicar no resultado: bot envia cartão da pergunta com toggle "marcar como respondida"

### RF06 — Marcar Pergunta como Respondida (Toggle)
- **Não existe mais** fluxo de texto-resposta do dono
- Dono tem botão toggle: **Marcar como respondida** ↔ **Desfazer**
- Ao marcar: inicia **timer de 15 segundos** antes de notificar o autor
- Durante os 15s: botão "Desfazer" visível para cancelar a notificação
- Ao desfazer: cancela timer e reverte estado no banco
- Após 15s: envia notificação ao autor da pergunta

### RF07 — Busca Pública (Inline Query)
- Prefixo de query: `cx <termo>` (busca por caixinhas públicas ativas)
- Qualquer usuário pode responder via resultado inline
- **Removida** a "Nuvem de Caixinhas" do menu principal

### RF08 — Mudar Idioma
- 3 idiomas: Português (pt), English (en), Español (es)
- Persiste no banco de dados

### RF09 — Comunicado (admin)
- Admin envia texto/mídia como comunicado
- Forward para todos os usuários registrados
- Relatório de entrega

### RF10 — Geração de Imagens
- Renderização em **escala 2x** com redução LANCZOS (anti-aliasing)
- Header com **gradiente azul** (escuro → claro)
- Avatar com **anel gradiente estilo Instagram Stories**
- Corpo claro com texto nítido
- Cartão de mensagem (500 × dinâmico): título + pergunta
- Cartão de caixinha (500 × dinâmico): título + CTA
- Story card (1080 × dinâmico): formato maior para compartilhamento

### RF11 — Cancelamento via Callback
- Botão "cancelar" em qualquer mensagem: **edita** a mensagem adicionando "❌ Cancelado" e remove os botões
- Se a edição falhar, envia mensagem standalone de cancelamento

## Requisitos Não-Funcionais

### RNF01 — Rate Limiting
- Limita requisições por usuário/tipo para prevenir spam

### RNF02 — Soft Delete
- Dados nunca são apagados fisicamente (coluna `deleted_at`)

### RNF03 — Dual Database
- Suporte a SQLite (desenvolvimento) e MariaDB (produção)
- Troca via configuração sem alteração de código

### RNF04 — Internacionalização
- Catálogo centralizado de mensagens com traduções
- Idioma do usuário persistido no banco

### RNF05 — Compatibilidade Deep Links
- Formato legado bloqueado: `?start=id_caixinha_<N>` (retorna aviso)
- Formato atual: `?start=cx-<uid>`
- Callbacks com método curto (≤ 64 bytes): `Classe__m__uid`

### RNF06 — Inline Query Routing
- Prefixos: `cx `, `mc `, `mc:c `, `p:<uid> `
- Resultados inline com `InputTextMessageContent` contendo deep links HTML
- Cache time = 1 para dados atualizados

### RNF07 — Notificação com Delay
- Notificações de "respondida" com timer de 15 segundos
- Permite undo (desfazer) antes da entrega
- Timer cancelado automaticamente ao desfazer
