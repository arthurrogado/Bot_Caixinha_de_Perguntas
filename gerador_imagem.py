from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def criarCartao(titulo, mensagem):
    # Abrir a imagem de base
    img = Image.open("base_mensagem.png")

    # Criar um objeto ImageDraw
    draw = ImageDraw.Draw(img)


    # Obtém o diretório atual (onde o script está sendo executado)
    diretorio_atual = os.getcwd()

    # Define o nome do arquivo da fonte
    nome_fonte = "arial.ttf"

    # Cria o caminho relativo para a fonte
    caminho_fonte = os.path.join(diretorio_atual, nome_fonte)
    print(caminho_fonte)

    # Escolher uma fonte e um tamanho
    fonte_titulo = ImageFont.truetype(caminho_fonte, 20)
    fonte_mensagem = ImageFont.truetype(caminho_fonte, 25)


    # Escrever o título na imagem
    xt, yt = [140, 75]
    titulo_quebrado = textwrap.wrap(titulo, width=30)
    for linha in titulo_quebrado:
        draw.text((xt, yt), linha, (255, 255, 255), font=fonte_titulo)
        yt += fonte_titulo.size


    # Quebrar o texto em linhas menores se for muito longo
    linhas = textwrap.wrap(mensagem, width=30)
    # Definir as coordenadas do canto superior esquerdo do texto
    x = 80
    y = 200
    # Desenhar cada linha do texto na imagem
    for linha in linhas:
        draw.text((x, y), linha, (0, 0, 0), font=fonte_mensagem, align="center")
        # Incrementar a coordenada y para a próxima linha
        y += fonte_mensagem.size

    return img


def criarCartaoCaixinha(titulo):
    img = Image.open("base_caixinha.png")

    # Criar um objeto ImageDraw
    draw = ImageDraw.Draw(img)

    fonte = ImageFont.truetype("arial.ttf", 30)
    #fonte = ImageFont.truetype("NotoColorEmoji-Regular.ttf", 30)

    # Escrever o título na imagem
    xt, yt = [40, 180]
    titulo_quebrado = textwrap.wrap(titulo, width=30)

    for linha in titulo_quebrado:
        draw.text((xt, yt), linha, (255, 255, 255), font=fonte)
        yt += fonte.size

    return img

""" # Exemplo de uso
titulo = "Título do cartão apenas para testar algo um pouco maior."
mensagem = "Olá, eu sou um cartão de mensagem. açslkdfjças çlakjsd fçlkasj dçlakjs dçflakjs f açlskdj fçalksjd fçlaskjd fçlaksdfj "

cartao = criarCartao(titulo, mensagem)
#cartao.show()

titulo = "TESTE: Faça uma pergunta anônima. Teste emoji "
cartao_caixinha = criarCartaoCaixinha(titulo)
cartao_caixinha.show() """