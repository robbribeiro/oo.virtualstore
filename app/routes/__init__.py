from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='app/views/html', static_folder='app/static')
app.secret_key = 'sua_chave_secreta'
socketio = SocketIO(app)

from app.routes.auth_routes import *
from app.routes.cart_routes import *
from app.routes.admin_routes import *
from app.routes.main_routes import * 