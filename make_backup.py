from config import ID_NUVEM

def send_backup(bot):
    bot.send_document(ID_NUVEM, 'database.db')