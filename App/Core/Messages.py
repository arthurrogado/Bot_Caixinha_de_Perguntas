"""Catálogo centralizado de mensagens com suporte a 3 idiomas (pt/en/es).

Uso nos componentes (via BaseComponent.self.msg):
    self.msg.MENU_PRINCIPAL.format(nome)
    self.msg.CRIAR_CAIXINHA
    self.msg.GENERIC_ERROR

Uso direto (ex: bot.py, fora de componentes):
    from App.Core.Messages import get_msg
    msg = get_msg(userid)
    text = msg.MENU_PRINCIPAL.format(nome)

Fallback chain: idioma do usuário → português (pt)
"""

# ─── Idiomas suportados ─────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    'pt': '🇧🇷 Português',
    'en': '🇺🇸 English',
    'es': '🇪🇸 Español',
}

DEFAULT_LANG = 'pt'

# ─── Triggers para cancelamento (reply keyboard) ────────────────────

CANCEL_TRIGGERS = frozenset({
    '❌ cancelar', '❌ cancel', '/cancel', 'cancel', 'cancelar',
})


# ─── Catálogo de mensagens ───────────────────────────────────────────

class Messages:
    """Catálogo de mensagens multi-idioma.

    Todas as mensagens ficam em ``_messages`` como dicts ``{lang: texto}``.
    Acesso via ``Messages.get(key, lang)`` ou pelo wrapper ``Msg``.
    """

    _messages = {

        # ── Constantes fixas ─────────────────────────────────────────
        'GENERIC_ERROR': {
            'pt': 'Oops! Ocorreu um erro inesperado.',
            'en': 'Oops! An unexpected error occurred.',
            'es': '¡Oops! Ocurrió un error inesperado.',
        },
        'OP_CANCELLED': {
            'pt': '⚠️ Operação cancelada',
            'en': '⚠️ Operation cancelled',
            'es': '⚠️ Operación cancelada',
        },
        'ADMIN_ONLY': {
            'pt': '⛔ Apenas administradores podem executar essa ação.',
            'en': '⛔ Only administrators can perform this action.',
            'es': '⛔ Solo los administradores pueden realizar esta acción.',
        },

        # ── Geral ─────────────────────────────────────────────────────
        'SIM': {
            'pt': '👍 Sim',
            'en': '👍 Yes',
            'es': '👍 Sí',
        },
        'NAO': {
            'pt': '❌ Não',
            'en': '❌ No',
            'es': '❌ No',
        },
        'EDITAR': {
            'pt': '✏️ Editar',
            'en': '✏️ Edit',
            'es': '✏️ Editar',
        },
        'CANCELAR': {
            'pt': '❌ Cancelar',
            'en': '❌ Cancel',
            'es': '❌ Cancelar',
        },
        'OK_CANCELADO': {
            'pt': '✅ Ok! Cancelado! ❌',
            'en': '✅ Ok! Canceled! ❌',
            'es': '✅ ¡Ok! ¡Cancelado! ❌',
        },
        'VOLTAR': {
            'pt': '⬅️ Voltar',
            'en': '⬅️ Back',
            'es': '⬅️ Volver',
        },

        # ── Menu principal ────────────────────────────────────────────
        'MENU_PRINCIPAL': {
            'pt': '👋😀 Olá {}, escolha alguma das opções abaixo:',
            'en': '👋😀 Hello {}, choose one of the options below:',
            'es': '👋😀 Hola {}, elige cualquiera de las siguientes opciones:',
        },
        'CRIAR_CAIXINHA': {
            'pt': '➕ Criar caixinha',
            'en': '➕ Create question box',
            'es': '➕ Crear caja de preguntas',
        },
        'MINHAS_CAIXINHAS': {
            'pt': '📦 Minhas caixinhas',
            'en': '📦 My question boxes',
            'es': '📦 Mis cajas de preguntas',
        },
        'RESPONDER_CAIXINHA': {
            'pt': '📝 Responder caixinha',
            'en': '📝 Answer question box',
            'es': '📝 Responder caja de preguntas',
        },
        'CAIXINHAS_CONCLUIDAS': {
            'pt': '✅ Caixinhas concluídas',
            'en': '✅ Completed question boxes',
            'es': '✅ Cajas de preguntas completadas',
        },
        'NUVEM_CAIXINHAS': {
            'pt': '☁️ Nuvem de caixinhas',
            'en': '☁️ Question box cloud',
            'es': '☁️ Nube de cajas',
        },
        'PESQUISAR_CAIXINHAS': {
            'pt': '🔎 Pesquisar caixinhas',
            'en': '🔎 Search question boxes',
            'es': '🔎 Buscar cajas',
        },
        'MUDAR_IDIOMA': {
            'pt': '🌐 Idioma | Language 🗣️',
            'en': '🌐 Idioma | Language 🗣️',
            'es': '🌐 Idioma | Language 🗣️',
        },
        'AJUDA': {
            'pt': '❓ Ajuda',
            'en': '❓ Help',
            'es': '❓ Ayuda',
        },

        # ── Idioma ────────────────────────────────────────────────────
        'SELECIONE_IDIOMA': {
            'pt': '🇧🇷 Alterar idioma\n🇺🇸 Change language\n🇲🇽🇪🇸 Cambiar idioma',
            'en': '🇧🇷 Alterar idioma\n🇺🇸 Change language\n🇲🇽🇪🇸 Cambiar idioma',
            'es': '🇧🇷 Alterar idioma\n🇺🇸 Change language\n🇲🇽🇪🇸 Cambiar idioma',
        },
        'CONFIRMACAO_MUDANCA_IDIOMA': {
            'pt': '✅ Idioma alterado para português 🇧🇷',
            'en': '✅ Language changed to English 🇺🇸',
            'es': '✅ Idioma cambiado a español 🇪🇸',
        },

        # ── Caixinha / CRUD ───────────────────────────────────────────
        'QUAL_O_TITULO_DA_CAIXINHA': {
            'pt': '🔤 Qual o título da caixinha?',
            'en': '🔤 What is the title of the question box?',
            'es': '🔤 ¿Cuál es el título de la caja de preguntas?',
        },
        'TITULO_MAX_80_CARACTERES': {
            'pt': '❌ O título deve ter no máximo 80 caracteres. Envie outro título...',
            'en': '❌ The title must have a maximum of 80 characters. Send another title...',
            'es': '❌ El título debe tener un máximo de 80 caracteres. Envíe otro título...',
        },
        'CAIXINHA_CRIADA_COM_SUCESSO': {
            'pt': '✅ Caixinha criada com sucesso!',
            'en': '✅ Question box created successfully!',
            'es': '✅ ¡Caja de preguntas creada con éxito!',
        },
        'CODIGO_DA_CAIXINHA': {
            'pt': '🔢 Código da caixinha: `{}`',
            'en': '🔢 Question box code: `{}`',
            'es': '🔢 Código de la caja de preguntas: `{}`',
        },
        'SUAS_CAIXINHAS': {
            'pt': 'Caixinhas concluídas: /caixinhas\\_concluidas\n\n\nSuas *CAIXINHAS* 📦:\n⬇️⬇️⬇️',
            'en': 'Completed question boxes: /caixinhas\\_concluidas\n\n\nYour *QUESTION BOXES* 📦:\n⬇️⬇️⬇️',
            'es': 'Cajas de preguntas completadas: /caixinhas\\_concluidas\n\n\nTus *CAJAS DE PREGUNTAS* 📦:\n⬇️⬇️⬇️',
        },
        'SUAS_CAIXINHAS_CONCLUIDAS': {
            'pt': 'Suas\n\n\nCAIXINHAS *CONCLUÍDAS* 📁:',
            'en': 'Your\n\n\n*COMPLETED* QUESTION BOXES 📁:',
            'es': 'Tus\n\n\nCAJAS DE PREGUNTAS *COMPLETADAS* 📁:',
        },
        'SEM_CAIXINHAS': {
            'pt': '📭 Você ainda não tem caixinhas. Crie uma!',
            'en': "📭 You don't have any question boxes yet. Create one!",
            'es': '📭 Aún no tienes cajas de preguntas. ¡Crea una!',
        },
        'VISUALIZAR_CAIXINHA': {
            'pt': '👁️ Visualizar caixinha',
            'en': '👁️ View question box',
            'es': '👁️ Ver caja de preguntas',
        },
        'MARCAR_CONCLUIDA': {
            'pt': '✅ Marcar como concluída',
            'en': '✅ Mark as completed',
            'es': '✅ Marcar como completada',
        },
        'REATIVAR_CAIXINHA': {
            'pt': '🔄 Reativar caixinha',
            'en': '🔄 Reactivate question box',
            'es': '🔄 Reactivar caja de preguntas',
        },
        'CAIXINHA_CONCLUIDA_OK': {
            'pt': '✅ Caixinha marcada como concluída!',
            'en': '✅ Question box marked as completed!',
            'es': '✅ ¡Caja de preguntas marcada como completada!',
        },
        'CAIXINHA_REATIVADA_OK': {
            'pt': '🆙 Caixinha reativada!',
            'en': '🆙 Question box reactivated!',
            'es': '🆙 ¡Caja de preguntas reactivada!',
        },
        'CAIXINHA_NAO_ENCONTRADA': {
            'pt': '❌ Caixinha {} não encontrada',
            'en': '❌ Question box {} not found',
            'es': '❌ Caja de preguntas {} no encontrada',
        },
        'ERRO_OPERACAO': {
            'pt': '❌🫢 Opa, alguma coisa deu errada.',
            'en': '❌🫢 Oops, something went wrong.',
            'es': '❌🫢 Ups, algo salió mal.',
        },

        # ── Responder caixinha (enviar pergunta) ──────────────────────
        'DIGITE_ID_CAIXINHA': {
            'pt': '🆔 Digite o ID da caixinha',
            'en': '🆔 Enter the question box ID',
            'es': '🆔 Introduce el ID de la caja de preguntas',
        },
        'OLA_BEM_VINDO_CAIXINHAS': {
            'pt': "👋 OLÁ! BEM VINDO(A) ÀS CAIXINHAS!\n\nQuer perguntar na caixinha do autor: {} ?\n\n📦 '*{}*'",
            'en': "👋 HELLO! WELCOME TO THE QUESTION BOXES!\n\nDo you want to ask in the author's box: {} ?\n\n📦 '*{}*'",
            'es': "👋 ¡HOLA! ¡BIENVENIDO(A) A LAS CAJAS DE PREGUNTAS!\n\n¿Quieres preguntar en la caja del autor: {} ?\n\n📦 '*{}*'",
        },
        'RESPONDER_ANONIMAMENTE': {
            'pt': '🤫 Responder anonimamente',
            'en': '🤫 Answer anonymously',
            'es': '🤫 Responder anónimamente',
        },
        'ENVIE_SUA_PERGUNTA': {
            'pt': '✅ Ok! Vamos lá!\n\nEnvie sua pergunta:',
            'en': "✅ Ok! Let's go!\n\nSend your question:",
            'es': '✅ ¡Ok! ¡Vamos allá!\n\nEnvía tu pregunta:',
        },
        'OK_AUTOR_NAO_VERA_IDENTIDADE': {
            'pt': '✅🙈 Ok, o autor não verá que a mensagem é sua! Vamos lá!\n\nEnvie sua pergunta:',
            'en': "✅🙈 Ok, the author will not see that the message is yours! Let's go!\n\nSend your question:",
            'es': '✅🙈 ¡Ok, el autor no verá que el mensaje es tuyo! ¡Vamos allá!\n\nEnvía tu pregunta:',
        },
        'PERGUNTA_MAX_180': {
            'pt': '🫢 A pergunta deve ter no máximo 180 caracteres. Envie outra...',
            'en': '🫢 The question must have a maximum of 180 characters. Send another...',
            'es': '🫢 La pregunta debe tener un máximo de 180 caracteres. Envíe otra...',
        },
        'CONFIRMA_ENVIO_PERGUNTA': {
            'pt': '😋 Me confirma se quer mandar mesmo a pergunta.',
            'en': '😋 Confirm if you want to send the question.',
            'es': '😋 Confirma si quieres enviar la pregunta.',
        },
        'ENVIE_SUA_PERGUNTA_EDITADA': {
            'pt': '📝 Envie sua pergunta editada:',
            'en': '📝 Send your edited question:',
            'es': '📝 Envía tu pregunta editada:',
        },
        'PERGUNTA_SALVA_COM_SUCESSO': {
            'pt': '✅ Pergunta salva com sucesso!',
            'en': '✅ Question saved successfully!',
            'es': '✅ ¡Pregunta guardada con éxito!',
        },
        'NAO_ENTENDI_CONFIRME_NOVAMENTE': {
            'pt': '🤔 Hmm, não entendi. Você quer responder a essa pergunta?',
            'en': "🤔 Hmm, I didn't understand. Do you want to answer this question?",
            'es': '🤔 Hmm, no entendí. ¿Quieres responder a esta pregunta?',
        },
        'AUTOR_ANONIMO': {
            'pt': '🙈 Anônimo 🫢',
            'en': '🙈 Anonymous 🫢',
            'es': '🙈 Anónimo 🫢',
        },
        'NOVA_PERGUNTA': {
            'pt': "🆙 <b>NOVA PERGUNTA NA CAIXINHA!</b>\n\n📦 <b>{}</b>\n\n📄 {}\n\n👤 Autor: {}\n\n<i>Baixe a imagem e poste no story!</i>",
            'en': "🆙 <b>NEW QUESTION IN THE BOX!</b>\n\n📦 <b>{}</b>\n\n📄 {}\n\n👤 Author: {}\n\n<i>Download the image and post to your story!</i>",
            'es': "🆙 <b>¡NUEVA PREGUNTA EN LA CAJA!</b>\n\n📦 <b>{}</b>\n\n📄 {}\n\n👤 Autor: {}\n\n<i>¡Descarga la imagen y publícala en tu story!</i>",
        },

        # ── Responder pergunta (owner responde) ───────────────────────
        'RESPONDER_PERGUNTA': {
            'pt': '↪️ Responder a uma pergunta',
            'en': '↪️ Answer a question',
            'es': '↪️ Responder a una pregunta',
        },
        'QUAL_ID_PERGUNTA': {
            'pt': '🆔 Qual o ID da pergunta?',
            'en': '🆔 What is the question ID?',
            'es': '🆔 ¿Cuál es el ID de la pregunta?',
        },
        'PERGUNTA_NAO_ENCONTRADA': {
            'pt': '🫢 Pergunta não encontrada',
            'en': '🫢 Question not found',
            'es': '🫢 Pregunta no encontrada',
        },
        'VOCE_NAO_AUTOR': {
            'pt': '❌ Você não é o autor da caixinha da pergunta em questão. Envie outra',
            'en': '❌ You are not the author of the question box in question. Send another',
            'es': '❌ No eres el autor de la caja de preguntas en cuestión. Envía otra',
        },
        'OLHA_PARECE_SUA_PERGUNTA_VAI_SER_RESPONDIDA': {
            'pt': "👀 Olha, parece que sua mensagem vai ser respondida!\n\n📄 *{}*\n\n👤 Autor da caixinha:\n{}",
            'en': "👀 Look, it looks like your message is going to be answered!\n\n📄 *{}*\n\n👤 Box author:\n{}",
            'es': "👀 Mira, parece que tu mensaje va a ser respondido!\n\n📄 *{}*\n\n👤 Autor de la caja:\n{}",
        },
        'DIGITE_SUA_RESPOSTA': {
            'pt': '💬 Digite a resposta para essa pergunta:',
            'en': '💬 Type your answer for this question:',
            'es': '💬 Escribe la respuesta para esta pregunta:',
        },
        'RESPOSTA_MAX_500': {
            'pt': '🫢 A resposta deve ter no máximo 500 caracteres. Envie outra...',
            'en': '🫢 The answer must be at most 500 characters. Send another one...',
            'es': '🫢 La respuesta debe tener como máximo 500 caracteres. Envía otra...',
        },
        'RESPOSTA_SALVA': {
            'pt': '✅ Resposta salva com sucesso!',
            'en': '✅ Answer saved successfully!',
            'es': '✅ ¡Respuesta guardada con éxito!',
        },
        'RESPONDER_OUTRA': {
            'pt': '🔎 Responder outra',
            'en': '🔎 Answer another',
            'es': '🔎 Responder otra',
        },
        'POSTAR_STORY': {
            'pt': '📱 Postar story',
            'en': '📱 Post story',
            'es': '📱 Publicar story',
        },
        'PESQUISAR_RESPOSTAS': {
            'pt': '🔎 Pesquisar respostas',
            'en': '🔎 Search answers',
            'es': '🔎 Buscar respuestas',
        },
        'MARCAR_RESPONDIDA': {
            'pt': '✅ Marcar como respondida',
            'en': '✅ Mark as answered',
            'es': '✅ Marcar como respondida',
        },
        'RESPONDIDA_DESFAZER': {
            'pt': '↩️ Respondida (desfazer)',
            'en': '↩️ Answered (undo)',
            'es': '↩️ Respondida (deshacer)',
        },
        'VER_PERGUNTAS': {
            'pt': '📋 Ver perguntas',
            'en': '📋 View questions',
            'es': '📋 Ver preguntas',
        },
        'SILENCIAR_NOTIFICACOES': {
            'pt': '🔕 Silenciar notificações',
            'en': '🔕 Mute notifications',
            'es': '🔕 Silenciar notificaciones',
        },
        'ATIVAR_NOTIFICACOES': {
            'pt': '🔔 Ativar notificações',
            'en': '🔔 Enable notifications',
            'es': '🔔 Activar notificaciones',
        },
        'CONFIRMAR_TITULO': {
            'pt': '📦 Título: *{}*\n\nConfirmar?',
            'en': '📦 Title: *{}*\n\nConfirm?',
            'es': '📦 Título: *{}*\n\n¿Confirmar?',
        },
        'RESPONDIDA_PENDENTE': {
            'pt': '✅ Marcada! O autor será notificado em 15s.',
            'en': '✅ Marked! The author will be notified in 15s.',
            'es': '✅ ¡Marcada! El autor será notificado en 15s.',
        },
        'DESMARCADA_RESPONDIDA': {
            'pt': '↩️ Desmarcada. O autor não será notificado.',
            'en': '↩️ Unmarked. The author will not be notified.',
            'es': '↩️ Desmarcada. El autor no será notificado.',
        },
        'INSTRUCAO_POSTAR': {
            'pt': 'Baixe a imagem e poste no story! 📱',
            'en': 'Download the image and post to your story! 📱',
            'es': '¡Descarga la imagen y publícala en tu story! 📱',
        },
        'STORY_INDISPONIVEL_BOT': {
            'pt': '⚠️ Post automático em Story não está disponível neste modo. Enviei a arte para postar manualmente.',
            'en': '⚠️ Automatic Story posting is not available in this mode. I sent the image so you can post manually.',
            'es': '⚠️ La publicación automática en Story no está disponible en este modo. Envié la imagen para publicarla manualmente.',
        },
        'AUTOR_AVISADO_RESPOSTA': {
            'pt': '✅ Autor da pergunta avisado sobre a resposta.',
            'en': '✅ The question author has been notified about the answer.',
            'es': '✅ Se notificó al autor de la pregunta sobre la respuesta.',
        },
        'SUA_PERGUNTA_RESPONDIDA': {
            'pt': "📣 Sua pergunta foi respondida!\n\n❓ *{}*\n\n💬 *{}*\n\n👤 Autor da caixinha:\n{}",
            'en': "📣 Your question has been answered!\n\n❓ *{}*\n\n💬 *{}*\n\n👤 Box author:\n{}",
            'es': "📣 ¡Tu pregunta fue respondida!\n\n❓ *{}*\n\n💬 *{}*\n\n👤 Autor de la caja:\n{}",
        },

        # ── Ajuda ─────────────────────────────────────────────────────
        'MSG_AJUDA': {
            'pt': (
                "❓ <b>Como funciona o Caixinha de Perguntas?</b>\n\n"
                "📦 <b>Criar caixinha</b> — Crie uma caixinha e compartilhe o link com amigos para receber perguntas\n\n"
                "📝 <b>Pesquisar caixinhas</b> — Encontre caixinhas públicas ou responda usando o código\n\n"
                "📋 <b>Minhas caixinhas</b> — Gerencie suas caixinhas, veja perguntas e marque como respondidas\n\n"
                "🌐 <b>Compartilhar em canais/grupos</b> — Use o modo inline (@bot + texto) para enviar sua caixinha diretamente em qualquer chat!\n\n"
                "🖼 <b>Story</b> — Baixe a imagem do cartão e poste no seu story\n\n"
                "🔒 <b>Visibilidade</b> — Caixinhas podem ser públicas (aparecem na busca) ou privadas (só com link)"
            ),
            'en': (
                "❓ <b>How does Question Box work?</b>\n\n"
                "📦 <b>Create box</b> — Create a box and share the link with friends to receive questions\n\n"
                "📝 <b>Search boxes</b> — Find public boxes or answer using the code\n\n"
                "📋 <b>My boxes</b> — Manage your boxes, view questions and mark as answered\n\n"
                "🌐 <b>Share in channels/groups</b> — Use inline mode (@bot + text) to send your box directly in any chat!\n\n"
                "🖼 <b>Story</b> — Download the card image and post to your story\n\n"
                "🔒 <b>Visibility</b> — Boxes can be public (appear in search) or private (link only)"
            ),
            'es': (
                "❓ <b>¿Cómo funciona Caja de Preguntas?</b>\n\n"
                "📦 <b>Crear caja</b> — Crea una caja y comparte el enlace con amigos para recibir preguntas\n\n"
                "📝 <b>Buscar cajas</b> — Encuentra cajas públicas o responde usando el código\n\n"
                "📋 <b>Mis cajas</b> — Gestiona tus cajas, ve preguntas y márcalas como respondidas\n\n"
                "🌐 <b>Compartir en canales/grupos</b> — ¡Usa el modo inline (@bot + texto) para enviar tu caja directamente en cualquier chat!\n\n"
                "🖼 <b>Story</b> — Descarga la imagen y publícala en tu story\n\n"
                "🔒 <b>Visibilidad</b> — Las cajas pueden ser públicas (aparecen en la búsqueda) o privadas (solo con enlace)"
            ),
        },

        # ── Admin ─────────────────────────────────────────────────────
        'COMUNICADO_QUAL_MSG': {
            'pt': '💬 Qual o comunicado? (texto ou texto e mídia)',
            'en': '💬 What is the announcement? (text or text and media)',
            'es': '💬 ¿Cuál es el comunicado? (texto o texto y multimedia)',
        },
        'COMUNICADO_PARA_QUEM': {
            'pt': '👤 Para quem enviar?',
            'en': '👤 Who to send to?',
            'es': '👤 ¿A quién enviar?',
        },
        'COMUNICADO_ENVIADO': {
            'pt': '✅ Comunicado enviado com sucesso!',
            'en': '✅ Announcement sent successfully!',
            'es': '✅ ¡Comunicado enviado con éxito!',
        },
        'SEM_PERMISSAO': {
            'pt': '❌ Você não tem permissão para acessar essa função.',
            'en': "❌ You don't have permission to access this function.",
            'es': '❌ No tienes permiso para acceder a esta función.',
        },

        # ── Canal obrigatório ─────────────────────────────────────────
        'ENTRE_NO_CANAL': {
            'pt': '📢 Para criar caixinhas, entre primeiro no nosso canal de atualizações!\n\n👇 Clique abaixo, entre no canal e tente novamente.',
            'en': '📢 To create question boxes, join our updates channel first!\n\n👇 Click below, join the channel and try again.',
            'es': '📢 Para crear cajas de preguntas, ¡únete primero a nuestro canal de actualizaciones!\n\n👇 Haz clic abajo, únete al canal e inténtalo de nuevo.',
        },
        'ENTRAR_NO_CANAL': {
            'pt': '📢 Entrar no canal',
            'en': '📢 Join channel',
            'es': '📢 Unirse al canal',
        },

        # ── Caixinha pública/privada ──────────────────────────────────
        'CAIXINHA_PUBLICA': {
            'pt': '🌐 Pública (aparece na busca)',
            'en': '🌐 Public (shows in search)',
            'es': '🌐 Pública (aparece en la búsqueda)',
        },
        'CAIXINHA_PRIVADA': {
            'pt': '🔒 Privada (só com link)',
            'en': '🔒 Private (link only)',
            'es': '🔒 Privada (solo con enlace)',
        },
        'TORNAR_PUBLICA': {
            'pt': '🌐 Tornar pública',
            'en': '🌐 Make public',
            'es': '🌐 Hacer pública',
        },
        'TORNAR_PRIVADA': {
            'pt': '🔒 Tornar privada',
            'en': '🔒 Make private',
            'es': '🔒 Hacer privada',
        },
        'ESCOLHA_VISIBILIDADE': {
            'pt': '👁️ Visibilidade da caixinha:\n\n🌐 <b>Pública</b> — aparece na busca global\n🔒 <b>Privada</b> — só quem tem o link pode ver',
            'en': '👁️ Box visibility:\n\n🌐 <b>Public</b> — shows in global search\n🔒 <b>Private</b> — only accessible via link',
            'es': '👁️ Visibilidad de la caja:\n\n🌐 <b>Pública</b> — aparece en la búsqueda global\n🔒 <b>Privada</b> — solo accesible por enlace',
        },

        # ── Caixinha concluída ────────────────────────────────────────
        'CAIXINHA_JA_CONCLUIDA': {
            'pt': '⚠️ Esta caixinha já foi concluída pelo autor e não aceita mais perguntas.',
            'en': '⚠️ This question box has been concluded by the author and no longer accepts questions.',
            'es': '⚠️ Esta caja de preguntas ya fue concluida por el autor y ya no acepta preguntas.',
        },

        # ── Pesquisar caixinhas (submenu) ─────────────────────────────
        'MENU_PESQUISAR': {
            'pt': '🔎 <b>Pesquisar Caixinhas Públicas</b>\n\nEscolha como deseja buscar:',
            'en': '🔎 <b>Search Public Question Boxes</b>\n\nChoose how to search:',
            'es': '🔎 <b>Buscar Cajas Públicas</b>\n\nElige cómo buscar:',
        },
        'MAIS_RECENTES': {
            'pt': '🕐 Mais recentes',
            'en': '🕐 Most recent',
            'es': '🕐 Más recientes',
        },
        'MAIS_PERGUNTADOS': {
            'pt': '🔥 Mais perguntados',
            'en': '🔥 Most asked',
            'es': '🔥 Más preguntados',
        },
        'EM_ALTA': {
            'pt': '📈 Em alta (24h)',
            'en': '📈 Trending (24h)',
            'es': '📈 En tendencia (24h)',
        },
        'RESPONDER_POR_CODIGO': {
            'pt': '🆔 Responder por código',
            'en': '🆔 Answer by code',
            'es': '🆔 Responder por código',
        },

        # ── Perguntas filtradas ───────────────────────────────────────
        'PERGUNTAS_NAO_RESPONDIDAS': {
            'pt': '⏳ Não respondidas',
            'en': '⏳ Unanswered',
            'es': '⏳ Sin responder',
        },
        'PERGUNTAS_RESPONDIDAS': {
            'pt': '✅ Respondidas',
            'en': '✅ Answered',
            'es': '✅ Respondidas',
        },

        # ── Comunicado melhorado ──────────────────────────────────────
        'COMUNICADO_CONTAGEM': {
            'pt': '📊 O comunicado será enviado para <b>{}</b> usuários.\n\nDigite <b>confirma enviar</b> para confirmar o envio:',
            'en': '📊 The announcement will be sent to <b>{}</b> users.\n\nType <b>confirma enviar</b> to confirm:',
            'es': '📊 El comunicado será enviado a <b>{}</b> usuarios.\n\nEscribe <b>confirma enviar</b> para confirmar:',
        },

        # ── Fuso horário ──────────────────────────────────────────────
        'SELECIONE_FUSO': {
            'pt': '🕐 Selecione seu fuso horário:',
            'en': '🕐 Select your timezone:',
            'es': '🕐 Selecciona tu zona horaria:',
        },
        'FUSO_ALTERADO': {
            'pt': '✅ Fuso horário alterado para <b>{}</b>',
            'en': '✅ Timezone changed to <b>{}</b>',
            'es': '✅ Zona horaria cambiada a <b>{}</b>',
        },

        # ── Painel Admin ──────────────────────────────────────────────
        'PAINEL_ADMIN': {
            'pt': '⚙️ Painel Administrativo',
            'en': '⚙️ Admin Panel',
            'es': '⚙️ Panel Administrativo',
        },
        'ESTATISTICAS': {
            'pt': '📊 Estatísticas',
            'en': '📊 Statistics',
            'es': '📊 Estadísticas',
        },
        'CONFIGURACOES': {
            'pt': '⚙️ Configurações',
            'en': '⚙️ Settings',
            'es': '⚙️ Configuraciones',
        },
        'BACKUP_AGORA': {
            'pt': '💾 Backup agora',
            'en': '💾 Backup now',
            'es': '💾 Backup ahora',
        },
        'BACKUP_ENVIADO': {
            'pt': '✅ Backup enviado com sucesso!',
            'en': '✅ Backup sent successfully!',
            'es': '✅ ¡Backup enviado con éxito!',
        },
        'BACKUP_ERRO': {
            'pt': '❌ Erro ao enviar backup.',
            'en': '❌ Error sending backup.',
            'es': '❌ Error al enviar backup.',
        },
    }

    @classmethod
    def get(cls, key: str, lang: str) -> str:
        """Retorna a mensagem para a chave e idioma dados.

        Fallback: idioma solicitado → português (pt).
        """
        entry = cls._messages.get(key)
        if not entry:
            return f' ~ {key} ~ '
        return entry.get(lang) or entry.get('pt', f' ~ {key} ~ ')


# ─── Wrapper com acesso por atributo ────────────────────────────────

class Msg:
    """Wrapper que expõe mensagens como atributos localizados.

    Exemplo:
        msg = get_msg(userid)
        msg.MENU_PRINCIPAL.format('João')
        msg.CRIAR_CAIXINHA
        msg.GENERIC_ERROR
    """

    __slots__ = ('_lang',)

    def __init__(self, lang: str) -> None:
        object.__setattr__(self, '_lang', lang)

    def __getattr__(self, key: str) -> str:
        return Messages.get(key, object.__getattribute__(self, '_lang'))


# ─── Cache de idioma e helpers ───────────────────────────────────────

_lang_cache: dict[int, str] = {}


def get_user_lang(userid: int) -> str:
    """Retorna o idioma do usuário, consultando o DB apenas na primeira vez."""
    if userid in _lang_cache:
        return _lang_cache[userid]
    try:
        from App.Database.users import Usuario
        lang = Usuario(userid).get_idioma() or DEFAULT_LANG
    except Exception:
        lang = DEFAULT_LANG
    _lang_cache[userid] = lang
    return lang


def set_user_lang(userid: int, lang: str) -> None:
    """Atualiza o cache de idioma e persiste no DB."""
    _lang_cache[userid] = lang
    try:
        from App.Database.users import Usuario
        Usuario(userid).set_idioma(lang)
    except Exception:
        pass


def get_msg(userid: int = None, lang: str = None) -> Msg:
    """Retorna um Msg localizado para o usuário ou idioma indicado.

    Args:
        userid: ID Telegram do usuário (consulta idioma do DB/cache)
        lang:   Idioma fixo (ignora userid se fornecido)
    """
    if lang:
        return Msg(lang)
    if userid:
        return Msg(get_user_lang(userid))
    return Msg(DEFAULT_LANG)
