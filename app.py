import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-muy-segura-cambiar-en-produccion' # Llave para las sesiones
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db' # Base de datos local

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuración de Gemini (lee de la variable de entorno o de apikey.txt)
def obtener_clave():
    if os.path.exists("apikey.txt"):
        return open("apikey.txt", "r", encoding="utf-8").read().strip()
    return os.environ.get("GEMINI_API_KEY", "")

client = genai.Client(api_key=obtener_clave())
MODELO = "gemini-3.5-flash-lite"

# --- MODELO DE BASE DE DATOS PARA USUARIOS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all() # Crea la base de datos si no existe

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_existente = User.query.filter_by(username=username).first()
        if user_existente:
            flash('El usuario ya existe.')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        nuevo_usuario = User(username=username, password=hashed_password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        login_user(nuevo_usuario)
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTA PRINCIPAL (EL CHAT CON EL AGENTE) ---
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    pregunta = data.get("message", "")
    
    if not pregunta:
        return jsonify({"response": "Mensaje vacío"}), 400

    try:
        # Generación de respuesta con Gemini
        respuesta = client.models.generate_content(
            model=MODELO,
            contents=pregunta,
        )
        return jsonify({"response": respuesta.text})
    except Exception as e:
        return jsonify({"response": f"Error al procesar la IA: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)