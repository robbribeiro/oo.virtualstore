from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import os
from app.controllers.application import Application
from app.controllers.db.datamanager import DataManager
from app.models.usuario import UsuarioComum
from app.models.produto import Produto

app = Flask(__name__, template_folder='app/views/html', static_folder='app/static')
app.secret_key = 'sua_chave_secreta_ultra_segura'  # Troque em produção!

# Inicializa o banco de dados e a aplicação
db_manager = DataManager()
ctl = Application()

# Inicializa o SocketIO com o app Flask
socketio = SocketIO(app)



#Configurações para upload de imagem do produto
diretorio_upload = 'app/static/img/produtos'
os.makedirs(diretorio_upload, exist_ok=True)
app.config['UPLOAD_FOLDER'] = diretorio_upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
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
            flash('Login realizado com sucesso!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('landing_page'))"Redirecionar login admin para dashboard"        
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

#-----------------------------------------------------------------------------
# Rota da Página Inicial (Após Login)

#-----------------------------------------------------------------------------

@app.route('/')
def landing_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    produtos = db_manager.produtos  # Lista de produtos do banco de dados
    return render_template('landing_page.html', produtos=produtos)

#-----------------------------------------------------------------------------
# Rotas do Admin (Acesso restrito)
#-----------------------------------------------------------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('landing_page'))
    
    produtos = db_manager.produtos
    return render_template('dashboard.html', produtos=produtos)

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if session.get('role')!= 'admin':
        return {'success': False, 'error': 'Acesso negado'}, 403
    # Processar imagem
    if 'imagem' not in request.files:
        return {'success': False, 'error': 'Nenhuma imagem enviada'}, 400
    
    file = request.files['imagem']
    if file.filename == '' or not allowed_file(file.filename):
        return {'success': False, 'error': 'Arquivo inválido'}, 400
    
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
    
    return {'success': True}

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
    app.run(host='0.0.0.0', port=8080, debug=True)
    