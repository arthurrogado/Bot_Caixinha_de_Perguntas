import sqlite3
from config import ID_NUVEM, NOME_BOT
from make_backup import send_backup

class DB:
    def __init__(self, bot = None, db = 'database.db'):
        self.bot = bot
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cursor = self.conn.cursor()
    
    def send_backup(self):
        if self.bot:
            with open('database.db', 'rb') as db:
                self.bot.send_document(ID_NUVEM, db, caption=f"#database \n {NOME_BOT}")
    
    # função para inserir, recebe dados e tabela e insere
    def inserir(self, tabela, colunas, dados):

        # transforma as listas em string e tira os [] dela
        colunas = str(colunas).replace('[', '').replace(']', '')

        # Define determinada quantidade de "?" para colocar os values 
        # (pode variar de acordo o número de colunas)
        placeholders = ", ".join([ '?' for x in dados ])
        
        sql = f'INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})'

        self.cursor.execute(sql, dados)
        self.conn.commit()
        # retornar se deu certo ou não
        if self.cursor.rowcount == 1:
            self.send_backup()
            # retorna o id do registro inserido
            return self.cursor.lastrowid
        return False
    
    def select(self, tabela, colunas, condicao = '1 = 1'):
        sql = f'SELECT {colunas} FROM {tabela} WHERE {condicao}'
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def update(self, tabela, coluna, valor, condicao):
        sql = f"UPDATE {tabela} SET {coluna} = '{valor}' WHERE {condicao}"
        self.cursor.execute(sql)
        self.conn.commit()
        # retornar se deu certo ou não
        if self.cursor.rowcount == 1:
            self.send_backup()
            return True
        return False


    # USUARIOS

    def checkUserExists(self, id):
        self.cursor.execute('SELECT * FROM usuarios WHERE id = ?', (id,))
        if self.cursor.fetchone():
            return True
        return False
    
    def insertUser(self, id, name):
        self.inserir('usuarios', ['id', 'nome'], [id, name])
    
    def getUser(self, id):
        self.cursor.execute('SELECT * FROM usuarios WHERE id = ?', (id,))
        return self.cursor.fetchone()
    
    def getIdioma(self, id):
        return self.select('usuarios', 'idioma', f'id = {id}')
    
    def setIdioma(self, userid, idioma):
        return self.update('usuarios', 'idioma', idioma, f'id = {userid}')

    def getAllUsers(self):
        return self.select('usuarios', '*')
    

    # CAIXINHAS

    def criarCaixinha(self, userid, titulo):
        return self.inserir('caixinhas', ['titulo', 'id_usuario'], [titulo, userid])

    def getCaixinha(self, id):
        return self.select('caixinhas', '*', f'id = {id}')

    def getCaixinhas(self, userid):
        return self.select('caixinhas', '*', f'id_usuario = {userid} AND concluida = 0')

    def concluirCaixinha(self, id):
        return self.update('caixinhas', 'concluida', 1, f"id = {id}")

    def reativarCaixinha(self, id):
        return self.update('caixinhas', 'concluida', 0, f"id = {id}")

    def getCaixinhasConcluidas(self, userid):
        return self.select('caixinhas', '*', f'id_usuario = {userid} AND concluida = 1')
    

    # PERGUNTAS

    def getPerguntas(self, id_caixinha):
        # retorna todas as perguntas que não foram respondidas, '0' ou 'NULL' das anteriores
        return self.select('perguntas', '*', f"id_caixinha = '{id_caixinha}' AND (respondida != 1 or respondida IS NULL) ")

    def getPergunta(self, id):
        return self.select('perguntas', '*', f"id = '{id}'")
    
    def getPerguntasRespondidas(self, id_caixinha):
        return self.select('perguntas', '*', f"id_caixinha = '{id_caixinha}' AND respondida = 1")

    def criarPergunta(self, id_caixinha, pergunta, id_usuario_autor, anonima):
        anonima = 1 if anonima else 0
        return self.inserir('perguntas', ['id_caixinha', 'pergunta', 'id_usuario_autor', 'anonima'], [id_caixinha, pergunta, id_usuario_autor, anonima])

    def __del__(self):
        self.conn.close()



