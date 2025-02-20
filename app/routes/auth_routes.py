from app.routes import app
from flask import render_template, request, redirect, url_for, session, flash
from app.controllers.db.datamanager import DataManager
from app.models.usuario import UsuarioComum

db_manager = DataManager()

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
                return redirect(url_for('landing_page'))        
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login')) 