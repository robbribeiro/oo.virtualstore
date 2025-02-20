class Carrinho:
    def __init__(self):
        self.itens = []

    def adicionar_item(self, produto_id, quantidade=1):
        """Adiciona um item ao carrinho ou incrementa sua quantidade se já existir"""
        # Procura se o produto já existe no carrinho
        item_existente = next((item for item in self.itens if item['produto_id'] == produto_id), None)
        
        if item_existente:
            # Se existe, apenas incrementa a quantidade
            item_existente['quantidade'] += quantidade
        else:
            # Se não existe, adiciona novo item
            self.itens.append({
                "produto_id": produto_id,
                "quantidade": quantidade
            })

    def remover_item(self, produto_id):
        """Remove um item do carrinho e retorna a quantidade que foi removida"""
        item = next((item for item in self.itens if item['produto_id'] == produto_id), None)
        quantidade_removida = 0
        
        if item:
            quantidade_removida = item['quantidade']
            self.itens = [i for i in self.itens if i['produto_id'] != produto_id]
            
        return quantidade_removida

    def limpar(self):
        """Limpa todos os itens do carrinho"""
        self.itens = []

    def to_dict(self):
        """Converte o carrinho para dicionário para salvar no JSON"""
        return self.itens

    @staticmethod
    def from_dict(itens):
        """Cria um carrinho a partir de um dicionário"""
        carrinho = Carrinho()
        carrinho.itens = itens
        return carrinho