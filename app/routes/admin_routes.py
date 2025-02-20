from app.routes import app, socketio
from flask import render_template, request, redirect, url_for, session, jsonify
from app.controllers.db.datamanager import DataManager
from app.models.produto import Produto
from app.models.usuario import Admin
import os

db_manager = DataManager()

# Configurações para upload de imagem do produto
diretorio_upload = os.path.join('app', 'static', 'img', 'produtos')
os.makedirs(diretorio_upload, exist_ok=True)
app.config['UPLOAD_FOLDER'] = diretorio_upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('landing_page'))
    
    produtos = db_manager.produtos
    return render_template('admin/dashboard.html', produtos=produtos)

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return {'success': False, 'error': 'Acesso negado'}, 403

    if 'imagem' not in request.files:
        return {'success': False, 'error': 'Nenhuma imagem enviada'}, 400
    
    file = request.files['imagem']
    if file.filename == '' or not allowed_file(file.filename):
        return {'success': False, 'error': 'Arquivo inválido'}, 400
    
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

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
    
    socketio.emit('produto_adicionado', {
        'produto_id': novo_produto.id,
        'nome': novo_produto.nome,
        'preco': novo_produto.preco,
        'estoque': novo_produto.estoque,
        'imagem': novo_produto.imagem
    })
    
    return {'success': True}

@app.route('/admin/edit/<int:product_id>', methods=['GET'])
def edit_product_form(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if not produto:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_product.html', produto=produto)

@app.route('/admin/edit/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if not produto:
        return redirect(url_for('admin_dashboard'))
    
    produto.nome = request.form['nome']
    produto.preco = float(request.form['preco'])
    produto.estoque = int(request.form['estoque'])
    
    if 'imagem' in request.files:
        file = request.files['imagem']
        if file.filename != '' and allowed_file(file.filename):
            # Remove a imagem antiga
            if produto.imagem:
                old_image_path = os.path.join('app', produto.imagem.lstrip('/'))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            produto.imagem = f"/static/img/produtos/{filename}"
    
    db_manager.salvar_dados()
    
    socketio.emit('produto_atualizado', {
        'produto_id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'estoque': produto.estoque,
        'imagem': produto.imagem
    })
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Não autorizado'}), 401
        
        user = next((u for u in db_manager.usuarios if u.id == session['user_id']), None)
        
        if not user or not isinstance(user, Admin):
            return jsonify({'success': False, 'message': 'Não autorizado'}), 401
        
        produto = next((p for p in db_manager.produtos if p.id == product_id), None)
        if produto:
            # Remove a imagem do produto
            if produto.imagem:
                image_path = os.path.join('app', produto.imagem.lstrip('/'))
                if os.path.exists(image_path):
                    os.remove(image_path)
                    
            db_manager.produtos = [p for p in db_manager.produtos if p.id != product_id]
            db_manager.salvar_dados()
            
            socketio.emit('produto_removido', {
                'produto_id': product_id
            })
            
            return jsonify({'success': True}), 200
            
        return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
    except Exception as e:
        print(f"Erro ao deletar produto: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao deletar produto: {str(e)}'}), 500

@socketio.on('atualizar_estoque')
def handle_estoque_update(data):
    product_id = data['produto_id']
    novo_estoque = data['estoque']
    
    produto = next((p for p in db_manager.produtos if p.id == product_id), None)
    if produto:
        produto.estoque = novo_estoque
        db_manager.salvar_dados()
        
        socketio.emit('estoque_atualizado', {
            'produto_id': product_id,
            'estoque': novo_estoque
        }, broadcast=True)

# Adicione as outras rotas do admin aqui... 