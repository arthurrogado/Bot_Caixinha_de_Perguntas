class SilentException(Exception):
    """Exceção que interrompe execução sem exibir mensagem genérica de erro ao usuário.
    
    Usar em guards (ex: PermissionMiddleware) onde a mensagem de erro já foi
    enviada antes do raise. O automatic_run() captura essa exceção e NÃO
    envia a mensagem genérica "Ocorreu um erro".
    """
    pass
