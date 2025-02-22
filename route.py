from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
import os
from app.controllers.application import Application
from app.controllers.db.datamanager import DataManager
from app.models.usuario import UsuarioComum, Admin
from app.models.produto import Produto

app = Flask(__name__, template_folder='app/views/html', static_folder='app/static')
app.secret_key = 'sua_chave_secreta'  # Substitua por uma chave secreta segura

# Inicializa o banco de dados
db_manager = DataManager()


# Inicializa o SocketIO com o app Flask
socketio = SocketIO(app)

#Configurações para upload de imagem do produto
diretorio_upload = 'app/static/img/produtos'
os.makedirs(diretorio_upload, exist_ok=True)
app.config['UPLOAD_FOLDER'] = diretorio_upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    # Verifica se o arquivo tem a extensão permitida
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

#-----------------------------------------------------------------------------
# Rotas de Autenticação
#-----------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if db_manager.buscar_usuario_por_username(username):
            flash('Usuário já existe!', 'error')
        else:
            novo_id = len(db_manager.usuarios) + 1
            novo_usuario = UsuarioComum(novo_id, username, password)
            db_manager.adicionar_usuario(novo_usuario)
            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db_manager.buscar_usuario_por_username(username)
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('landing_page'))        
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Pega a URL anterior
    previous_url = request.referrer
    session.clear()
    
    # Se veio da página do carrinho, redireciona de volta para ela
    if previous_url and 'carrinho' in previous_url:
        return redirect(url_for('carrinho'))
    
    # Caso contrário, vai para a página inicial
    return redirect(url_for('landing_page'))

#-----------------------------------------------------------------------------
# Rotas da Página Inicial
#-----------------------------------------------------------------------------

@app.route('/')
def landing_page():    
    produtos = db_manager.produtos
    cart_count = 0
    
    if 'user_id' in session:
        user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
        if user:
            cart_count = sum(item['quantidade'] for item in user.carrinho.itens)
    
    return render_template('landing_page.html', produtos=produtos, cart_count=cart_count)

#-----------------------------------------------------------------------------
# Rotas do Carrinho
#-----------------------------------------------------------------------------

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return '', 401

    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    if not user:
        return '', 401
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)

    if user and produto and produto.estoque > 0:
        user.carrinho.adicionar_item(product_id)
        produto.estoque -= 1
        db_manager.salvar_dados()
        
        # Emite atualização do estoque via WebSocket
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
    
    # Obtém a quantidade que foi removida
    quantidade_removida = user.carrinho.remover_item(product_id)
    
    # Devolve os itens ao estoque
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if produto:
        produto.estoque += quantidade_removida
        
        # Emite atualização do estoque via WebSocket
        socketio.emit('estoque_atualizado', {
            'produto_id': product_id,
            'estoque': produto.estoque
        })
    
    db_manager.salvar_dados()
    return '', 200

@app.route('/carrinho')
def carrinho():
    if 'user_id' not in session:
        return render_template('carrinho.html', itens=None, total=0, cart_count=0)
    
    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
    if not user:
        return render_template('carrinho.html', itens=None, total=0, cart_count=0)
    
    # Prepara os itens do carrinho com informações completas dos produtos
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

#-----------------------------------------------------------------------------
# Rotas do Admin
#-----------------------------------------------------------------------------

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('landing_page'))
    
    produtos = db_manager.produtos
    return render_template('/admin/dashboard.html', produtos=produtos)

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect(url_for('landing_page'))

    if 'imagem' in request.files:
        file = request.files['imagem']
        if file.filename != '' and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Criar produto
            novo_id = len(db_manager.produtos) + 1
            novo_produto = Produto(
                id=novo_id,
                nome=request.form['nome'],
                preco=float(request.form['preco']),
                estoque=int(request.form['estoque']),
                imagem=f"/static/img/produtos/{filename}" 
            )
            
            db_manager.produtos.append(novo_produto)
            db_manager.salvar_dados()
            
            # Emite evento de novo produto via WebSocket
            socketio.emit('produto_adicionado', {
                'produto_id': novo_produto.id,
                'nome': novo_produto.nome,
                'preco': novo_produto.preco,
                'estoque': novo_produto.estoque,
                'imagem': novo_produto.imagem
            })
            
            return {'success': True}
    
    return {'success': False, 'message': 'Imagem não fornecida ou inválida.'}, 400

@app.route('/admin/edit/<int:product_id>')
def edit_product_form(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('landing_page'))
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if not produto:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('/admin/edit_product.html', produto=produto)

@app.route('/admin/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('landing_page'))
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if not produto:
        return redirect(url_for('admin_dashboard'))
    
    # Pega o estoque antigo para comparação
    estoque_antigo = produto.estoque
    
    # Atualizar dados básicos
    produto.nome = request.form['nome']
    produto.preco = float(request.form['preco'])
    produto.estoque = int(request.form['estoque'])
    
    # Atualizar imagem se uma nova for enviada
    if 'imagem' in request.files:
        file = request.files['imagem']
        if file.filename != '' and allowed_file(file.filename):
            # Remove a imagem antiga
            if produto.imagem:
                old_image_path = os.path.join('app', produto.imagem.lstrip('/'))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Salva a nova imagem
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            produto.imagem = f"/static/img/produtos/{filename}"
    
    db_manager.salvar_dados()
    
    # Emite evento de produto atualizado via WebSocket
    socketio.emit('produto_atualizado', {
        'produto_id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'estoque': produto.estoque,
        'imagem': produto.imagem,
        'estoque_alterado': estoque_antigo == 0 and produto.estoque > 0  # Indica se o produto voltou a ter estoque
    })
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('landing_page'))
    
    # Busca o usuário na lista de usuários
    user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
       
    # Usar o método remover_produto do DataManager
    if db_manager.remover_produto(product_id):
        socketio.emit('produto_removido', {
            'produto_id': product_id
        })
        return jsonify({'success': True}), 200
    
#-----------------------------------------------------------------------------
# WebSocket para Atualização em Tempo Real
#-----------------------------------------------------------------------------
@socketio.on('atualizar_estoque')
def handle_estoque_update(data):
    product_id = data['produto_id']
    novo_estoque = data['estoque']
    
    # Atualizar no banco de dados
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if produto:
        produto.estoque = novo_estoque
        db_manager.salvar_dados()
        
        # Emitir atualização para todos os clientes
        emit('estoque_atualizado', {
            'produto_id': product_id,
            'estoque': novo_estoque
        }, broadcast=True)
        
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', False)
    
    socketio.run(app, host=host, port=port, debug=debug)
    