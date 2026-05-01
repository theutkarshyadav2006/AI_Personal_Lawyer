import os
from flask import Flask
from dotenv import load_dotenv
import os
print("TEMPLATE PATH:", os.path.join(os.getcwd(), "templates"))
# Load .env using absolute path so it always works
_env_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
load_dotenv(_env_path, override=True)

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    # Secret key — MUST be set in production env vars
    secret = os.getenv("SECRET_KEY")
    if not secret:
        import secrets
        secret = secrets.token_hex(32)
        print("WARNING: SECRET_KEY not set. Sessions will reset on restart. Set SECRET_KEY in environment variables.")
    app.secret_key = secret

    # Configure Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'legal_ecosystem.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configure Server-side sessions (fixes 4KB cookie limit for Chatbot)
    from flask_session import Session
    session_dir = os.path.join(basedir, 'flask_session')
    os.makedirs(session_dir, exist_ok=True)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = session_dir
    Session(app)

    # Initialize Extensions
    from database.extensions import db, login_manager
    from database.models import User

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from blueprints.auth import auth_bp
    from blueprints.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app

from flask_socketio import SocketIO
from database.models import Message

app = create_app()

# Threading mode works on all platforms for local dev
# Production uses gevent via Procfile (gunicorn --worker-class gevent)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Socket.IO Event Handlers for Real-Time Chat
@socketio.on('join_case')
def on_join(data):
    from flask_socketio import join_room
    room = str(data['case_id'])
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    from database.extensions import db
    from flask_socketio import emit

    case_id = data['case_id']
    sender_id = data['sender_id']
    content = data['content']

    with app.app_context():
        msg = Message(case_id=case_id, sender_id=sender_id, content=content)
        db.session.add(msg)
        db.session.commit()
        timestamp_str = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')

    emit('receive_message', {
        'sender_id': sender_id,
        'content': content,
        'timestamp': timestamp_str
    }, room=str(case_id))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host="127.0.0.1", port=port, debug=True, use_reloader=True, allow_unsafe_werkzeug=True)
