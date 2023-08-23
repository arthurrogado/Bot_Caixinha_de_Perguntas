def MENU(menu_key, lang='pt', *params ):

    #print('*** *params', *params)

    menus = {
        "MAIN_MENU": {
            "pt": "MENU PRINCIPAL",
            "en": "MAIN MENU",
        },

        'sim': {
            'pt': '👍 Sim',
            'en': '👍 Yes',
            'es': '👍 Sí'
        },
        'nao': {
            'pt': '❌ Não',
            'en': '❌ No',
            'es': '❌ No'
        },
        'editar': {
            'pt': "✏️ Editar",
            'en': "✏️ Edit",
            'es': "✏️ Editar"
        },
        'cancelar': {
            'pt': '❌ Cancelar',
            'en': '❌ Cancel',
            'es': '❌ Cancelar'
        },
        'ok_cancelado': {
            'pt': '✅ Ok! Cancelado! ❌',
            'en': '✅ Ok! Canceled! ❌',
            'es': '✅ ¡Ok! ¡Cancelado! ❌'
        },


        'responder_anonimamente': {
            'pt': '🤫 Responder anonimamente',
            'en': '🤫 Answer anonymously',
            'es': '🤫 Responder anónimamente'
        },

        # Adicione mais entradas de menu conforme necessário
        "voce_nao_tem_permissao_para_acessar_essa_funcao": {
            "pt": "❌ Você não tem permissão para acessar essa função.",
            "en": "❌ You don't have permission to access this function.",
            "es": "❌ No tienes permiso para acceder a esta función.",
        },
        "menu_principal": {
            "pt": "👋😀 Olá {}, escolha alguma das opções abaixo:",
            'en': "👋😀 Hello {}, choose some of the below options:",
            'es': "👋😀 Hola {}, elige cualquiera de las siguientes opciones:"
        },

        # Markup pagina inicial
        "criar_caixinha": {
            'pt': '📚 Criar caixinha',
            'en': '📚 Create question box',
            'es': '📚 Crear caja de preguntas',
        },
        
        "minhas_caixinhas": {
            "pt": "📦 Minhas caixinhas",
            'en': "📦 My question boxes",
            'es': "📦 Mis cajas de preguntas",
        },
        'responder_caixinha': {
            'pt': '📝 Responder caixinha',
            'en': '📝 Answer question box',
            'es': '📝 Responder caja de preguntas',
        },
        'caixinhas_concluidas': {
            'pt': '✅ Caixinhas concluídas',
            'en': '✅ Completed question boxes',
            'es': '✅ Cajas de preguntas completadas',
        },
        'mudar_idioma': {
            'pt': '🗣️ Mudar idioma',
        },

        'confirmacao_mudanca_idioma': {
            'pt': '✅ Idioma alterado para português 🇧🇷',
            'en': '✅ Language changed to english 🇺🇸',
            'es': '✅ Idioma cambiado a español 🇪🇸'
        },

        'digite_id_caixinha': {
            'pt': '🆔 Digite o ID da caixinha',
            'en': '🆔 Enter the question box ID',
            'es': '🆔 Introduce el ID de la caja de preguntas'
        },

        # Markup Caixinha
        'visualizar_caixinha': {
            'pt': '👁️ Visualizar caixinha',
            'en': '👁️ View question box',
            'es': '👁️ Ver caja de preguntas'
        },
        'marcar_concluida': {
            'pt': '✅ Marcar como concluída',
            'en': '✅ Mark as completed',
            'es': '✅ Marcar como completada'
        },
        'reativar_caixinha': {
            'pt': '🔄 Reativar caixinha',
            'en': '🔄 Reactivate question box',
            'es': '🔄 Reactivar caja de preguntas'
        },

        # Markup responder pergunta
        'responder_pergunta': {
            'pt': '↪️ Responder a uma pergunta',
            'en': '↪️ Answer a question',
            'es': '↪️ Responder a una pregunta'
        },


        ## CLASSES ----------------------------------------------------

        # criarCaixinha()
        'qual_o_titulo_da_caixinha': {
            'pt': '🔤 Qual o título da caixinha?',
            'en': '🔤 What is the title of the question box?',
            'es': '🔤 ¿Cuál es el título de la caja de preguntas?'
        },
        'titulo_max_80_caracteres': {
            'pt': '❌ O título deve ter no máximo 80 caracteres. Envie outro título...',
            'en': '❌ The title must have a maximum of 80 characters. Send another title...',
            'es': '❌ El título debe tener un máximo de 80 caracteres. Envíe otro título...'
        },
        'caixinha_criada_com_sucesso': {
            'pt': '✅ Caixinha criada com sucesso!',
            'en': '✅ Question box created successfully!',
            'es': '✅ Caja de preguntas creada con éxito!'
        },
        'imagem_da_caixinha': {
            'pt': '🖼️ Imagem da caixinha',
            'en': '🖼️ Question box image',
            'es': '🖼️ Imagen de la caja de preguntas'
        },
        'codigo_da_caixinha': {
            'pt': '🔢 Código da caixinha: `{}`',
            'en': '🔢 Question box code: `{}`',
            'es': '🔢 Código de la caja de preguntas: `{}`'
        },
        
        # getCaixinhas()
        'suas_caixinhas': {
            'pt': "Caixinhas concluídas: /caixinhas\_concluidas \n\n\n Suas *CAIXINHAS* 📦: \n ⬇️⬇️⬇️",
            'en': "Completed question boxes: /caixinhas_concluidas \n\n\n Your *QUESTION BOXES* 📦: \n ⬇️⬇️⬇️",
            'es': "Cajas de preguntas completadas: /caixinhas\_concluidas \n\n\n Tus *CAJAS DE PREGUNTAS* 📦: \n ⬇️⬇️⬇️"
        },

        ## responderCAixinha
        'caixinha_nao_encontrada': {
            'pt': '❌ Caixinha {} não encontrada',
            'en': '❌ Question box {} not found',
            'es': '❌ Caja de preguntas {} no encontrada'            
        },
        'ola_bem_vindo_caixinhas': {
            'pt': "📦 OLÁ! BEM VINDO(A) ÀS CAIXINHAS! \n Quer perguntar na caixinha do autor: {} ? \n\n * 📦 '{}' *",
            'en': "📦 HELLO! WELCOME TO THE QUESTION BOXES! \n Do you want to ask in the author's box: {} ? \n\n * 📦 '{}' *",
            'es': "📦 ¡HOLA! ¡BIENVENIDO(A) A LAS CAJAS DE PREGUNTAS! \n ¿Quieres preguntar en la caja del autor: {} ? \n\n * 📦 '{}' *"
        },
        'envie_sua_pergunta': {
            'pt': '✅ Ok! Vamos lá! \n\n Envie sua pergunta:',
            'en': '✅ Ok! Let’s go! \n\n Send your question:',
            'es': '✅ ¡Ok! ¡Vamos allá! \n\n Envía tu pregunta:'
        },
        'anonimamente': {
            'pt': '🤫 Anonimamente',
            'en': '🤫 Anonymously',
            'es': '🤫 Anónimamente'
        },
        'ok_autor_nao_vera_identidade': {
            'pt': "✅🙈 Ok, o autor não verá que a mensagem é sua! Vamos lá! \n\n Envie sua pergunta:",
            'en': "✅🙈 Ok, the author will not see that the message is yours! Let's go! \n\n Send your question:",
            'es': "✅🙈 ¡Ok, el autor no verá que el mensaje es tuyo! ¡Vamos allá! \n\n Envía tu pregunta:"
        },
        'nao_entendi_confirme_novamente': {
            'pt': "🤔 Hmm, não entendi. Você quer responder a essa pergunta?",
            'en': "🤔 Hmm, I didn't understand. Do you want to answer this question?",
            'es': "🤔 Hmm, no entendí. ¿Quieres responder a esta pregunta?"
        },
        'pergunta_max_180': {
            'pt': "🫢 A pergunta deve ter no máximo 180 caracteres. Envie outra...",
            'en': "🫢 The question must have a maximum of 180 characters. Send another...",
            'es': "🫢 La pregunta debe tener un máximo de 180 caracteres. Envíe otra..."
        },
        'confirma_envio_pergunta': {
            'pt': "😋 Me confirma se quer mandar mesmo a pergunta.",
            'en': "😋 Confirm if you want to send the question.",
            'es': "😋 Confirma si quieres enviar la pregunta."
        },
        'envie_sua_pergunta_editada': {
            'pt': "📝 Envie sua pergunta editada:",
            'en': "📝 Send your edited question:",
            'es': "📝 Envía tu pregunta editada:"
        },
        'pergunta_salva_com_sucesso': {
            'pt': "✅ Pergunta salva com sucesso!",
            'en': "✅ Question saved successfully!",
            'es': "✅ ¡Pregunta guardada con éxito!"
        },
        'autor_anonimo': {
            'pt': "🙈 Anônimo 🫢",
            'en': "🙈 Anonymous 🫢",
            'es': "🙈 Anónimo 🫢"
        },
        'nova_pergunta': {
            'pt': "🆙 __NOVA PERGUNTA NA CAIXINHA\!__ \n\n *📦 '{}'* \n\n 📄 Mensagem: * {} * \n\n 🆔 ID mensagem: {} \n 👤 Autor mensagem: {} \n\n _Baixe a imagem e anexe em um story_",
            'en': "🆙 __NEW QUESTION IN THE BOX\!__ \n\n *📦 '{}'* \n\n 📄 Message: * {} * \n\n 🆔 Message ID: {} \n 👤 Message author: {} \n\n _Download the image and attach it to a story_",
            'es': "🆙 __¡NUEVO PREGUNTA EN LA CAJA\!__ \n\n *📦 '{}'* \n\n 📄 Mensaje: * {} * \n\n 🆔 ID del mensaje: {} \n 👤 Autor del mensaje: {} \n\n _Descarga la imagen y adjúntala a una historia_"
        },

        ## responderPergunta
        'qual_id_pergunta': {
            'pt': "🆔 Qual o ID da pergunta?",
            'en': "🆔 What is the question ID?",
            'es': "🆔 ¿Cuál es el ID de la pregunta?"
        },
        'perguntar_nao_encontrada': {
            'pt': "🫢 Pergunta não encontrada",
            'en': "🫢 Question not found",
            'es': "🫢 Pregunta no encontrada"
        },
        'voce_nao_autor': {
            'pt': "❌ Você não é o autor da caixinha da pergunta em questão. Envie outra",
            'en': "❌ You are not the author of the question box in question. Send another",
            'es': "❌ No eres el autor de la caja de preguntas en cuestión. Envía otra"
        },
        'olha_parece_sua_pergunta_vai_ser_respondida': {
            'pt': "👀 Olha, parece que sua mensagem vai ser respondida\! \n\n 📄 * {} * \n\n 👤 Autor da caixinha: \n {} ",
            'en': "👀 Look, it looks like your message is going to be answered\! \n\n 📄 * {} * \n\n 👤 Box author: \n {} ",
            'es': "👀 Mira, parece que tu mensaje va a ser respondido\! \n\n 📄 * {} * \n\n 👤 Autor de la caja: \n {} "
        }


        
    }

    try:
        return menus[menu_key][lang].format(*params)
    except:
        try:
            return menus[menu_key].get('pt').format(*params)
        except:
            return f' ~ {menu_key} ~'