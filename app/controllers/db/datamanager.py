import json
import os
from pathlib import Path
from app.models.usuario import UsuarioComum, Admin
from app.models.produto import Produto

class DataManager:
    def __init__(self):
        self.db_path = Path("app/controllers/db/database.json")
        self.usuarios = []
        self.produtos = []
        self.carregar_dados()

    def carregar_dados(self):
        if self.db_path.exists():
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                # Carregar usuários
                for user_data in data["usuarios"]:
                    if user_data["role"] == "admin":
                        usuario = Admin(user_data["id"], user_data["username"], user_data["password"])
                    else:
                        usuario = UsuarioComum(user_data["id"], user_data["username"], user_data["password"])
                    usuario.carrinho = user_data["carrinho"]
                    self.usuarios.append(usuario)
                # Carregar produtos
                for produto_data in data["produtos"]:
                    produto = Produto(
                        produto_data["id"],
                        produto_data["nome"],
                        produto_data["preco"],
                        produto_data["estoque"],
                        produto_data["imagem"]
                    )
                    self.produtos.append(produto)

    def salvar_dados(self):
        data = {
            "usuarios": [
                {
                    "id": user.id,
                    "username": user.username,
                    "password": user.password,
                    "role": user.role,
                    "carrinho": user.carrinho
                } for user in self.usuarios
            ],
            "produtos": [
                {
                    "id": produto.id,
                    "nome": produto.nome,
                    "preco": produto.preco,
                    "estoque": produto.estoque,
                    "imagem": produto.imagem
                } for produto in self.produtos
            ]
        }
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=4)
            
    def remover_produto(self, product_id):
        produto = next((p for p in self.produtos if p.id == product_id), None)
    
        if produto:
            print(f"[DEBUG] Produto encontrado: {produto.nome} (ID: {produto.id})")
        
            # Remover imagem
            if produto.imagem:
                caminho_imagem = os.path.join('app', produto.imagem.lstrip('/'))
                print(f"[DEBUG] Caminho da imagem: {caminho_imagem}")
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)
                    print("[DEBUG] Imagem excluída com sucesso.")
        
            # Remover do banco de dados
            self.produtos = [p for p in self.produtos if p.id != product_id]
            self.salvar_dados()
            print("[DEBUG] Produto removido e banco de dados salvo.")
        else:
            print(f"[ERRO] Produto com ID {product_id} não encontrado.")

    # Métodos para manipulação de dados:
    def adicionar_usuario(self, usuario):
        self.usuarios.append(usuario)
        self.salvar_dados()

    def buscar_usuario_por_username(self, username):
        for usuario in self.usuarios:
            if usuario.username == username:
                return usuario
        return None
    
    