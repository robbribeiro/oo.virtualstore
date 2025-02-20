from app.routes import app, socketio
from flask import render_template, redirect, url_for, session, jsonify, flash
from app.controllers.db.datamanager import DataManager

db_manager = DataManager()

@app.route('/carrinho')
def carrinho():
    if 'user_id' not in session:
        flash('Por favor, faça login para acessar seu carrinho', 'info')
        return redirect(url_for('login'))
    
    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    if not user:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('login'))
    
    itens_carrinho = []
    total = 0
    
    for item in user.carrinho.itens:
        produto = next((p for p in db_manager.produtos if p.id == item['produto_id']), None)
        if produto:
            itens_carrinho.append({
                'produto': produto,
                'quantidade': item['quantidade']
            })
            total += produto.preco * item['quantidade']
    
    return render_template('carrinho.html', itens=itens_carrinho, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)

    if user and produto and produto.estoque > 0:
        user.carrinho.adicionar_item(product_id)
        produto.estoque -= 1
        db_manager.salvar_dados()
        
        socketio.emit('estoque_atualizado', {
            'produto_id': product_id,
            'estoque': produto.estoque
        })
        
        return '', 200
    return '', 400

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'user_id' not in session:
        return '', 401
    
    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    if not user:
        return '', 401
    
    quantidade_removida = user.carrinho.remover_item(product_id)
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if produto:
        produto.estoque += quantidade_removida
        
        socketio.emit('estoque_atualizado', {
            'produto_id': product_id,
            'estoque': produto.estoque
        })
    
    db_manager.salvar_dados()
    return '', 200

@app.route('/get_cart_total')
def get_cart_total():
    if 'user_id' not in session:
        return jsonify({'total': 0})
    
    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    if not user:
        return jsonify({'total': 0})
    
    total = 0
    for item in user.carrinho.itens:
        produto = next((p for p in db_manager.produtos if p.id == item['produto_id']), None)
        if produto:
            total += produto.preco * item['quantidade']
    
    return jsonify({'total': total})

@app.route('/finalizar_compra', methods=['POST'])
def finalizar_compra():
    if 'user_id' not in session:
        return '', 401
    
    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    if not user:
        return '', 401
    
    user.carrinho.limpar()
    db_manager.salvar_dados()
    
    return '', 200

# Adicione as outras rotas do carrinho aqui... 