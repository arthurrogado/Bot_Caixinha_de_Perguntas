import telebot
from telebot.formatting import escape_markdown
from telebot.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove, 
    BotCommand, 
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat
)


import io

from db import DB
from config import *
from gerador_imagem import *
from make_backup import send_backup
from traducoes import MENU

bot = telebot.TeleBot(TOKEN)

#####################

# FUNÇÕES

def gerar_markup(botoes, sufixo = None):
    markup = InlineKeyboardMarkup()
    for i in range( len(botoes) ):
        markup.add(
            InlineKeyboardButton(botoes[i][0], callback_data=botoes[i][1] + (f'_{sufixo}' if sufixo else ''))
        )
    markup.row_width = 2
    return markup

def gerar_teclado(lista_botoes):
    markup = ReplyKeyboardMarkup()
    markup.row_width = 1
    for i in lista_botoes:
        markup.add(
            KeyboardButton(text=i)
        )
    return markup

def limparTeclado(userid):
    # apenas limpar o teclado do usuário, sem mensagens
    msg = bot.send_message(userid, '...', reply_markup=ReplyKeyboardRemove())
    bot.delete_message(userid, msg.message_id)

def getIdioma(userid):
    db = DB()
    try:
        return db.getIdioma(userid)[0][0]
    except:
        return 'pt'


def getUserInfo(userid):
    user = bot.get_chat(userid)
    return {
        'id': user.id,
        'nome': user.first_name + (' ' + user.last_name if user.last_name else ''), # se tiver sobrenome coloca
        'username': user.username if user.username else '-no username-',
        'link': f'https://t.me/{user.username}' if user.username else '-no username-',
        'link_user_id': f"[Usuário:](tg://user?id={userid})" # para usar em markdown
    }

def getUserInfoInText(userid):
    user = getUserInfo(userid)
    return f"[User:](tg://user?id={userid}) { escape_markdown(user['nome']) } \- @{ escape_markdown(user['username']) }"

def getAutorPergunta(id_pergunta):
    # retorna o nome do autor da pergunta
    # se não existir, retorna None
    # se for anônima, retorna "Anônimo"
    db = DB()
    pergunta = db.getPergunta(id_pergunta)
    if pergunta:
        pergunta = pergunta[0]
    else:
        return None
    
    if pergunta[5] == 1:
        # pergunta anônima
        return "🙈 Anônimo 🕵️‍♂️"

    id_autor = pergunta[2]
    return getUserInfoInText(id_autor)



# FUNÇÕES DE MENSAGENS ------------------

def enviarCartaoPergunta(userid, id_caixinha, id_pergunta, caption = None):

    # pegar dados da caixinha
    db = DB()
    caixinha = db.getCaixinha(id_caixinha)[0]
    titulo_caixinha = caixinha[1]

    # pegar dados da pergunta
    pergunta = db.getPergunta(id_pergunta)[0]

    texto_mensagem = pergunta[3]
    id_autor = pergunta[2]

    cartao = criarCartao(titulo_caixinha, texto_mensagem) # Objeto de imagem (png)
    
    # ENVIAR IMAGEM SEM SALVAR NO SERVIDOR COMO ARQUIVO
    # cria um buffer
    buffer = io.BytesIO()
    # salva o png nesse buffer
    cartao.save(buffer, format='PNG')
    # nomeia o buffer, colocando a extensão .png
    buffer.name = 'cartao.png'
    # volta para o início do buffer
    buffer.seek(0)

    if caption == None:
        autor = getAutorPergunta(pergunta[0])
        caption = f"📦 '_{ escape_markdown(titulo_caixinha) }_': \n\n 📄 { escape_markdown(texto_mensagem) } \n\n Autor: { autor }"
    bot.send_document(userid, buffer, caption=caption, parse_mode='MarkdownV2', reply_markup = markup_responder_pergunta(id_caixinha, getIdioma(userid)))
    
def conhecer_bots(userid):
    texto = """🤖 Quer conhecer outros bots? Então siga o canal @BotNewsBR"""
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton('🤖 Conhecer outros bots', url='https://t.me/BotNewsBR'))
    bot.send_message(userid, texto, parse_mode='Markdown', reply_markup = markup)

def doacao(userid):
    texto = "🥺 Seria muito bom ter a sua ajudinha para manter o bot 🤖 \n\n 🔗 Pode usar o link: http://mpago.la/1mT2FKs \n\n 📲 Ou a chave aleatória pix _(clique nela para copiar)_ \n 👉 `99ebe931-26c7-4956-add5-becc77874e57`"
    bot.send_message(userid, texto, parse_mode='MarkdownV2')

def ajuda(userid):
    message = "❓ Esse bot serve para você criar caixinhas de perguntas e compartilhar com seus amigos. Para começar, digite /start"
    message += "\n\n📚 Para criar uma caixinha, clique em 'Criar caixinha'"
    message += "\n\n📦 Para ver suas caixinhas, clique em 'Minhas caixinhas'"
    message += "\n\n🖼 Você consegue gerar um png das mensagens recebidas na caixinha clicando em 👁️ visualizar caixinha."
    message += "\n\n📄 Para responder a uma pergunta, clique em 'Responder a uma pergunta' e selecione "
    bot.send_message(userid, message, reply_markup=markup_pagina_inicial())

def mudar_idioma(userid):
    message = "🇧🇷 Alterer idioma \n 🇺🇸 Change language \n 🇲🇽🇪🇸 Alterar língua"
    bot.send_message(userid, message, reply_markup=markup_mudar_idioma())


# -----------------------------------------



# MARKUPS ----------------------
def markup_pagina_inicial(idioma = 'pt'):
    return gerar_markup([
        [MENU('criar_caixinha', idioma), 'criar_caixinha'],
        [MENU('minhas_caixinhas', idioma), 'minhas_caixinhas'],
        [MENU('caixinhas_concluidas', idioma), 'caixinhas_concluidas'],
        ['🌐 Idioma | Language 🗣️', 'mudar_idioma']
    ])

def markup_mudar_idioma():
    return gerar_markup([
        ['🇧🇷🇵🇹 Português', 'mudar_idioma_pt'],
        ['🇲🇽🇪🇸 Español', 'mudar_idioma_es'],
        ['🇺🇸 English', 'mudar_idioma_en']
    ])

def markup_caixinha(id_caixinha, idioma = 'pt'):
    return gerar_markup([
        [ MENU('visualizar_caixinha', idioma) , 'visualizar_caixinha'],
        [ MENU('marcar_concluida', idioma) , 'marcar_concluida']
    ], id_caixinha)

def markup_caixinha_concluida(id_caixinha, idioma = 'pt') :
    return gerar_markup([
    [ MENU('visualizar_caixinha', idioma) , 'visualizar_caixinha'],
    [ MENU('reativar_caixinha', idioma) , 'reativar_caixinha']
], id_caixinha)

def markup_responder_pergunta(id_caixinha, idioma = 'pt'):
    return gerar_markup([
        [ MENU('responder_pergunta', idioma) , 'responder_pergunta']
    ],  sufixo = f"id_caixinha_{id_caixinha}")



# menu principal

def menu_principal(userid):
    nome = bot.get_chat(userid).first_name
    idioma =  getIdioma(userid)
    mensagem = MENU('menu_principal', idioma, *(nome,))
    bot.send_message(userid, mensagem, reply_markup=markup_pagina_inicial(idioma=idioma))






## COMANDOS DO BOT -----------------------------------------------------

comandos_comuns = [
    BotCommand("start", "🤖 Inicia o bot"),
    BotCommand("ajuda", "❓ Mostra a ajuda"),
    BotCommand("conhecer_bots", "🤖 Conhecer outros bots"),
    BotCommand("doacao", "💰 Ajudar desenvolvedor pobre 😢"),
]

# Definir os comandos de acordo o usuário
bot.set_my_commands(comandos_comuns, scope = BotCommandScopeAllPrivateChats())

# agora do arthur
comandos_arthur = [
    BotCommand("start", "🤖 Inicia o bot"),
    BotCommand("ajuda", "❓ Mostra a ajuda"),
    BotCommand("conhecer_bots", "🤖 Conhecer outros bots"),
    BotCommand("doacao", "💰 Ajudar desenvolvedor pobre 😢"),
    BotCommand("comunicado", "📢 Enviar comunicado para todos os usuários")
]
bot.set_my_commands(comandos_arthur, scope = BotCommandScopeChat(ID_ARTHUR) )


# enviar comunicado - admin arthur
@bot.message_handler(commands=['comunicado'])
def comunicado(msg):
    userid = msg.chat.id
    if userid == ID_ARTHUR:
        enviarComunicado(userid)
    else:
        bot.send_message(userid, "Você não tem permissão para usar esse comando")

# Comando de start personalizado
@bot.message_handler(commands=['start'])
def start(msg):
    userid = msg.chat.id
    
    db = DB()
    if db.checkUserExists(userid) == False:
        db.insertUser(userid, msg.chat.first_name)

    try:
        if msg.text.split()[1].startswith('id_caixinha_'):
            id_caixinha = msg.text.split()[1].split('_')[2] # ex: id_caixinha_1
            responderCaixinha(userid, id_caixinha)
    except Exception as e:
        # não foi passado nenhum parâmetro
        menu_principal(userid)
        print('** ERRO', e)

# ----------------------------------------------

# START - Qualquer mensagem
@bot.message_handler(func=lambda m: True)
def start(msg):
    userid = msg.chat.id
    
    db = DB()
    if db.checkUserExists(userid) == False:
        db.insertUser(userid, msg.chat.first_name)

    cases = {
        "/conhecer_bots": lambda: conhecer_bots(userid),
        "/doacao": lambda: doacao(userid),
        "/ajuda": lambda: ajuda(userid),
    }

    try:
        cases[msg.text]()
    except Exception as e:
        # se a mensagem inicia com um numeral, reponderCaixinha
        if msg.text.isnumeric():
            id_caixinha = msg.text.split()[0]
            responderCaixinha(userid, int(id_caixinha))
        else:
            menu_principal(userid)



# ----------------------------------------------


# CALLBACKS #######################################
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    userid = call.from_user.id
    if call.data == 'criar_caixinha':
        criarCaixinha(userid)
        
    elif call.data == 'minhas_caixinhas':
        getCaixinhas(userid)
        pass
    
    elif call.data == 'caixinhas_concluidas':
        getCaixinhasConcluidas(userid)
        pass

    elif call.data.startswith('visualizar_caixinha'):
        id_caixinha = call.data.split('_')[2]
        getPerguntasFromCaixinha(userid, id_caixinha)
        pass

    elif call.data.startswith('marcar_concluida'):
        id_caixinha = call.data.split('_')[2]
        marcarCaixinhaConcluida(userid, id_caixinha, call)
        pass

    elif call.data.startswith('reativar_caixinha'):
        id_caixinha = call.data.split('_')[2]
        reativarCaixinha(userid, id_caixinha, call)
        pass

    elif call.data.startswith('responder_pergunta'):
        id_caixinha = call.data.split('_id_caixinha_')[1]
        responderPergunta(userid, id_caixinha)

    elif call.data == 'mudar_idioma':
        mudar_idioma(userid)

    elif call.data.startswith('mudar_idioma_'):
        db = DB()
        idioma_escolhido = call.data.split('mudar_idioma_')[1]
        if db.setIdioma(userid, idioma_escolhido):
            bot.send_message(userid, MENU('confirmacao_mudanca_idioma', idioma_escolhido))
            menu_principal(userid)
        else:
            bot.send_message(userid, '❌🫢 Opa, alguma coisa foi errada \n Oopps, something wrong!')








# -------- CLASSES escopos -----------

class criarCaixinha:
    def __init__(self, userid):
        self.userid = userid
        self.titulo = None

        msg = bot.send_message(userid, MENU('qual_o_titulo_da_caixinha', getIdioma(self.userid)))
        bot.register_next_step_handler(msg, self.receber_titulo)

    def receber_titulo(self, msg):
        titulo = msg.text
        if (len(titulo) > 80):
            msg = bot.send_message(self.userid, MENU('titulo_max_80_caracteres', getIdioma(self.userid)))
            bot.register_next_step_handler(msg, self.receber_titulo)
            return
        self.titulo = titulo
        self.salvar_caixinha()
        
    def salvar_caixinha(self):
        db = DB(bot)
        id_caixinha_criada = db.criarCaixinha(self.userid, self.titulo)
        if id_caixinha_criada != False:
            bot.send_message(self.userid, MENU('caixinha_criada_com_sucesso', getIdioma(self.userid)))
            
            # gerar png da caixinha
            img = criarCartaoCaixinha(self.titulo)
            io_buffer = io.BytesIO()
            img.save(io_buffer, format='PNG')
            io_buffer.seek(0)
            io_buffer.name = 'caixinha.png'
            link_start_caixinha = f"https://t.me/{bot.get_me().username}?start=id_caixinha_{id_caixinha_criada}"
            bot.send_document(self.userid, io_buffer, caption=f" { MENU('codigo_da_caixinha', getIdioma(self.userid), id_caixinha_criada) } \n\n '📦 { escape_markdown(self.titulo) }' \n\n 🔗 `{link_start_caixinha}`", parse_mode='MarkdownV2', reply_markup=markup_caixinha(id_caixinha_criada, getIdioma(self.userid)))
            

class getCaixinhas:
    def __init__(self, userid):
        self.userid = userid
        self.caixinhas = None

        db = DB()
        self.caixinhas = db.getCaixinhas(self.userid)
        self.enviar_caixinhas()

    def enviar_caixinhas(self):
        bot.send_message(self.userid, MENU('suas_caixinhas', getIdioma(self.userid)), parse_mode='MarkdownV2')
        for caixinha in self.caixinhas:
            titulo = caixinha[1]
            id_caixinha = caixinha[0]
            #bot.send_message(self.userid, f"""📦 <b> {titulo} </b> \n 🔗 <code> https://t.me/{bot.get_me().username}?start=id_caixinha_{id_caixinha} </code>""", parse_mode='HTML' , reply_markup = markup_caixinha(id_caixinha))
            
            # enviar imagem da caixinha
            img = criarCartaoCaixinha(titulo)
            io_buffer = io.BytesIO()
            img.save(io_buffer, format='PNG')
            io_buffer.seek(0)
            io_buffer.name = 'caixinha.png'
            bot.send_document(self.userid, io_buffer, caption=f"""📦 <b> {titulo} </b> \n\n 🔗 <code> https://t.me/{bot.get_me().username}?start=id_caixinha_{id_caixinha} </code>""", parse_mode='HTML' , reply_markup = markup_caixinha(id_caixinha, getIdioma(self.userid)))
        pass

class getCaixinhasConcluidas:
    def __init__(self, userid):
        self.userid = userid
        self.caixinhas = None

        db = DB()
        self.caixinhas = db.getCaixinhasConcluidas(self.userid)
        self.enviar_caixinhas()

    def enviar_caixinhas(self):
        bot.send_message(self.userid, "Suas \n\n\n CAIXINHAS *CONCLUÍDAS* 📁:", parse_mode='Markdown')
        for caixinha in self.caixinhas:
            titulo = caixinha[1]
            id_caixinha = caixinha[0]
            bot.send_message(self.userid, f"""📦 <b> {titulo} </b> \n 🔗 <code> https://t.me/{bot.get_me().username}?start=id_caixinha_{id_caixinha} </code>""", parse_mode='HTML' , reply_markup = markup_caixinha_concluida(id_caixinha))
        pass

class marcarCaixinhaConcluida:
    def __init__(self, userid, id_caixinha, call):
        self.userid = userid
        self.id_caixinha = id_caixinha
        self.call = call

        db = DB(bot)
        if db.concluirCaixinha(self.id_caixinha):
            bot.answer_callback_query(self.call.id, "✅ Caixinha marcada como concluída!")
            bot.edit_message_reply_markup(self.userid, self.call.message.message_id, reply_markup = markup_caixinha_concluida(self.id_caixinha))
        else:
            bot.answer_callback_query(self.call.id, "❌ Erro ao marcar caixinha como concluída", show_alert=True)

class reativarCaixinha:
    def __init__(self, userid, id_caixinha, call):
        self.userid = userid
        self.id_caixinha = id_caixinha
        self.call = call

        db = DB(bot)
        if db.reativarCaixinha(self.id_caixinha):
            bot.answer_callback_query(self.call.id, "🆙 Caixinha reativada!")
            bot.edit_message_reply_markup(self.userid, self.call.message.message_id, reply_markup = markup_caixinha(self.id_caixinha, getIdioma(self.userid)) )
        else:
            bot.answer_callback_query(self.call.id, "❌ Erro ao reativar caixinha", show_alert=True)



class getPerguntasFromCaixinha:
    def __init__(self, userid, id_caixinha):
        self.userid = userid
        self.id_caixinha = id_caixinha
        self.perguntas = None

        self.db = DB()
        self.perguntas = self.db.getPerguntas(self.id_caixinha)
        self.enviar_perguntas()

    def enviar_perguntas(self):
        caixinha = self.db.getCaixinha(self.id_caixinha)
        caixinha = caixinha[0] # pegar a primeira e única caixinha
        titulo_caixinha = caixinha[1]
        message = f"📦 Perguntas caixinha: \n\n Título: *_ { escape_markdown(titulo_caixinha) } _* \n\n MENSAGENS DA CAIXINHA: \n\n"
        
        enviar_as_perguntas = lambda: bot.send_message(self.userid, message, parse_mode='MarkdownV2', reply_markup = markup_responder_pergunta(self.id_caixinha, getIdioma(self.userid)))


        for pergunta in self.perguntas:
            if(len(message) < 3900):
                id_pergunta = pergunta[0]
                texto_pergunta = pergunta[3]
                id_autor = pergunta[2]
                anonimo = pergunta[5] == 1

                # se for anônimo, não identificar o autor
                if anonimo:
                    autor_texto = "🙈 Anônimo 🫢"
                else:
                    autor_texto = getUserInfoInText(id_autor)
                message += f" `{id_pergunta}`  * {escape_markdown(texto_pergunta) } * \n {autor_texto} \n\n"

            else:
                enviar_as_perguntas()
                message = ""

        # enviar
        try:
            enviar_as_perguntas()
        except Exception as e:
            print('ERRO', e)
            bot.send_message(self.userid, "Erro ao enviar perguntas")
            bot.send_message(self.userid, message)


class responderCaixinha:
    # enviar mensagem para caixinha
    def __init__(self, userid, id_caixinha):
        self.userid = userid
        self.id_caixinha = id_caixinha
        self.id_pergunta_criada = None
        self.pergunta = None
        self.anonimo = False
        self.db = DB(bot)

        self.markup_sim_nao_anonimo = gerar_teclado([ MENU('sim', getIdioma(self.userid)), MENU('nao', getIdioma(self.userid)) , MENU('responder_anonimamente', getIdioma(self.userid)) ])

        self.callback_query = None

        caixinha = self.db.getCaixinha(self.id_caixinha)
        if caixinha == False or caixinha == []:
            bot.send_message(self.userid, MENU('caixinha_nao_encontrada', getIdioma(self.userid), [self.id_caixinha]) )
            return
        
        self.sim = MENU('sim', getIdioma(self.userid))
        self.nao = MENU('nao', getIdioma(self.userid))
        self.editar = MENU('editar', getIdioma(self.userid))
        self.cancelar = MENU('cancelar', getIdioma(self.userid))
        
        self.caixinha = caixinha[0]
        self.titulo = self.caixinha[1]
        self.autor = self.caixinha[2]

        message = MENU('ola_bem_vindo_caixinhas', getIdioma(self.userid), getUserInfoInText(self.autor), escape_markdown(self.titulo) )
        msg = bot.send_message(self.userid, message, reply_markup = self.markup_sim_nao_anonimo, parse_mode='Markdown')
        bot.register_next_step_handler(msg, self.confirmar_caixinha)

    def confirmar_caixinha(self, msg):
        if MENU('sim', getIdioma(self.userid)) in msg.text:
            msg = bot.send_message(self.userid, MENU('envie_sua_pergunta', getIdioma(self.userid)) , reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, self.receber_pergunta)
        elif MENU('nao', getIdioma(self.userid)) in msg.text:
            bot.send_message(self.userid, MENU('ok_cancelado', getIdioma(self.userid)) , reply_markup=ReplyKeyboardRemove())
            return
        elif MENU('responder_anonimamente', getIdioma(self.userid)) in msg.text:
            self.anonimo = True
            msg = bot.send_message(self.userid, MENU('ok_autor_nao_vera_identidade') , reply_markup= ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, self.receber_pergunta)
        else:
            msg = bot.send_message(self.userid, MENU('nao_entendi_confirme_novamente') , reply_markup = self.markup_sim_nao_anonimo)
            bot.register_next_step_handler(msg, self.confirmar_caixinha)

    def receber_pergunta(self, msg):
        pergunta = msg.text
        if (len(pergunta) > 180):
            msg = bot.send_message(self.userid, MENU('pergunta_max_180', getIdioma(self.userid)) )
            bot.register_next_step_handler(msg, self.receber_pergunta)
            return
        
        self.pergunta = pergunta
        msg = bot.send_message(self.userid, MENU('confirma_envio_pergunta', getIdioma(self.userid)) , reply_markup = gerar_teclado([ 
            self.sim, self.editar, self.cancelar
        ]) )
        bot.register_next_step_handler(msg, self.salvar_pergunta)

    def salvar_pergunta(self, msg):
        confirmacao = msg.text

        if self.editar in confirmacao:
            msg = bot.send_message(self.userid, MENU('envie_sua_pergunta_editada', getIdioma(self.userid)) , reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, self.receber_pergunta)
            return
        
        elif self.cancelar in confirmacao:
            bot.send_message(self.userid, MENU('ok_cancelado', getIdioma(self.userid)) , reply_markup=ReplyKeyboardRemove())
            return
        
        elif self.sim in confirmacao:
            self.id_mensagem_criada = self.db.criarPergunta(self.id_caixinha, self.pergunta, self.userid, self.anonimo)
            bot.send_message(self.userid, MENU('pergunta_salva_com_sucesso', getIdioma(self.userid)) , reply_markup=ReplyKeyboardRemove())

            if self.anonimo:
                autor = MENU('autor_anonimo', getIdioma(self.userid))
            else:
                autor = getUserInfoInText(self.userid)

            # Notificar o autor da caixinha de uma nova mensagem
            texto = MENU(
                'nova_pergunta',
                getIdioma(self.userid),
                escape_markdown(self.titulo),
                escape_markdown(self.pergunta),
                self.id_mensagem_criada,
                autor
            )
            msg = bot.send_message(self.autor, text = texto, reply_markup = markup_responder_pergunta(self.id_caixinha), parse_mode='Markdown')
            bot.delete_message(self.userid, msg.message_id)
            # enviar imagem:
            try:
                enviarCartaoPergunta(self.autor, self.id_caixinha, self.id_mensagem_criada, texto)
            except Exception as e:
                print('ERRO na notificação ao dono da caixinha: \n\n', e)

        else: 
            msg = bot.send_message(self.userid, MENU('nao_entendi_confirme_novamente') , reply_markup = gerar_teclado([ 
                self.sim, self.editar, self.cancelar
            ]) )
            bot.register_next_step_handler(msg, self.salvar_pergunta)

class responderPergunta:
    def __init__(self, userid, id_caixinha):
        self.userid = userid
        self.db = DB(bot)

        teclado = [MENU('cancelar', getIdioma(self.userid))]
        self.perguntas = self.db.getPerguntas(id_caixinha)
        for pergunta in self.perguntas:
            teclado.append(f"{pergunta[0]} # {pergunta[3]}")
            pass
        
        msg = bot.send_message(self.userid, MENU('qual_id_pergunta', getIdioma(self.userid)) , reply_markup = gerar_teclado(teclado) )
        bot.register_next_step_handler(msg, self.pegar_id_pergunta)

    def pegar_id_pergunta(self, msg):
        if MENU('cancelar', getIdioma(self.userid)) in msg.text:
            bot.send_message(self.userid, MENU('ok_cancelado', getIdioma(self.userid)) , reply_markup=ReplyKeyboardRemove())
            return

        id_pergunta = msg.text.split('#')[0].strip() # pegar o id da pergunta, ignorando o resto
        pergunta = self.db.getPergunta(id_pergunta)

        if pergunta == []:
            msg = bot.send_message(self.userid, MENU('pergunta_nao_encontrada', getIdioma(self.userid)) )
            bot.register_next_step_handler(msg, self.pegar_id_pergunta)
            return
        
        pergunta = pergunta[0]
        id_caixinha = pergunta[1]
        texto_mensagem = pergunta[3]
        id_autor = pergunta[2]
        titulo_caixinha = self.db.getCaixinha(id_caixinha)[0][1]

        # verificar se o autor da caixinha da pergunta em questão é o usuário atual
        caixinha = self.db.getCaixinha(id_caixinha)
        id_autor_caixinha = caixinha[0][2]
        if id_autor_caixinha != self.userid:
            msg = bot.send_message(self.userid, MENU('voce_nao_autor', getIdioma(self.userid)) )
            bot.register_next_step_handler(msg, self.pegar_id_pergunta)
            return

        msg = bot.send_message(self.userid, f"📦 '_{ escape_markdown(titulo_caixinha) }_': \n\n 📄 { escape_markdown(texto_mensagem) } ", parse_mode='MarkdownV2', reply_markup = ReplyKeyboardRemove())
        bot.delete_message(self.userid, msg.message_id)

        # enviar imagem da pergunta / mensagem:
        enviarCartaoPergunta( self.userid, id_caixinha, id_pergunta)

        # avisar autor da mensagem
        try:
            if id_autor != self.userid: # não enviar mensagem para si mesmo
                mensagem_aviso = MENU(
                    'olha_parece_sua_pergunta_vai_ser_respondida',
                    getIdioma(self.userid),
                    escape_markdown(texto_mensagem),
                    getUserInfoInText(self.userid),
                )

                bot.send_message(id_autor, mensagem_aviso , parse_mode='MarkdownV2')
        except:
            # mas pode ter parado de usar o bot, ou ser bot teste que não tem acesso ao usuário
            pass



class enviarComunicado:
    def __init__(self, userid):
        if userid != ID_ARTHUR:
            bot.send_message(userid, "🚫 Acesso negado")
            return
        self.userid = userid
        self.db = DB(bot)

        msg = bot.send_message(self.userid, "💬 Qual o comunicado? (texto ou texto e mídia)", reply_markup = ReplyKeyboardRemove() )
        bot.register_next_step_handler(msg, self.salvar_titulo)

    def salvar_titulo(self, msg):
        self.comunicado = msg
        msg = bot.send_message(self.userid, "👤 Para quem enviar?", reply_markup = gerar_teclado(['Todos']))
        bot.register_next_step_handler(msg, self.salvar_destinatario)

    def salvar_destinatario(self, msg):
        self.destinatario = msg
        if self.destinatario.text == 'Todos':
            # pegar todos os usuários
            usuarios = self.db.getAllUsers()
            if usuarios == False:
                bot.send_message(self.userid, "😢 Nenhum usuário encontrado", reply_markup = ReplyKeyboardRemove())
                return
            
            texto = f"📨 Enviando comunicado para todos os {len(usuarios)} usuários..."
            for usuario in usuarios:
                try:
                    #bot.copy_message(usuario[0], self.userid, self.comunicado.message_id)
                    bot.forward_message(usuario[0], self.userid, self.comunicado.message_id)
                except:
                    pass
                

        bot.send_message(self.userid, "✅ Comunicado enviado com sucesso!", reply_markup = ReplyKeyboardRemove())



bot.infinity_polling()