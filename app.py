from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import folium
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelo de Usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    details = db.Column(db.String(500), nullable=True)



with app.app_context():
    db.create_all()  # Asegúrate de que las tablas existan

    # Crea usuarios de ejemplo
    users = [
        User(username='user1', password=generate_password_hash('password1'), latitude=-16.5000, longitude=-68.1500, details='Productor de café'),
        User(username='user2', password=generate_password_hash('password2'), latitude=-16.6000, longitude=-68.2000, details='Productor de maíz'),
        User(username='user3', password=generate_password_hash('password3'), latitude=-16.7000, longitude=-68.3000, details='Productor de arroz'),
        User(username='user4', password=generate_password_hash('password4'), latitude=-16.8000, longitude=-68.4000, details='Productor de quinua'),
        User(username='user5', password=generate_password_hash('password5'), latitude=-16.9000, longitude=-68.5000,  details='Productor de frutas'),
    ]

    # Agrega los usuarios a la base de datos
    for user in users:
        db.session.add(user)

    # Guarda los cambios
    db.session.commit()
    print("Usuarios creados exitosamente.")
# Configuración de Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ruta de registro de usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe. Intenta con otro.', 'danger')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Ruta de inicio de sesión
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('map'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register_user():  # Renombramos la función
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe. Intenta con otro.', 'danger')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Ruta del mapa
@app.route('/map')
@login_required
def map():
    # Definir la ubicación inicial del mapa (puedes cambiar estas coordenadas)
    map_center = [-16.5000, -68.1500]  # Ejemplo: La Paz, Bolivia
    my_map = folium.Map(location=map_center, zoom_start=10)

    # Agregar marcadores para los productores registrados
    users = User.query.all()
    for user in users:
        if user.latitude and user.longitude:
            popup_content = f"""
            <div style="text-align: center;">
                <img src="{user.photo_url}" alt="Foto de {user.username}" style="width: 100px; height: 100px; border-radius: 50%;">
                <h3>{user.username}</h3>
                <p>{user.details}</p>
            </div>
            """
            folium.Marker(
                [user.latitude, user.longitude],
                popup=popup_content,
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(my_map)

    # Renderizar el HTML del mapa
    map_html = my_map._repr_html_()
    return render_template('map.html', map_html=map_html)

# Ruta para cerrar sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Inicializa Flask-SocketIO
socketio = SocketIO(app)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@socketio.on('send_message')
def handle_send_message(data):
    emit('receive_message', data, broadcast=True)  # Envía el mensaje a todos los usuarios conectados

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear tablas en la base de datos si aún no existen
    socketio.run(app, debug=True)
