from app.routes import app
from flask import render_template, session, redirect, url_for
from app.controllers.db.datamanager import DataManager

db_manager = DataManager()

@app.route('/')
def landing_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    produtos = [p for p in db_manager.produtos if p.estoque > 0]
    return render_template('landing_page.html', produtos=produtos) 