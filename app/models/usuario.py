class Usuario:
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.carrinho = []

class UsuarioComum(Usuario):
    def __init__(self, id, username, password):
        super().__init__(id, username, password, "user")

class Admin(Usuario):
    def __init__(self, id, username, password):
        super().__init__(id, username, password, "admin")