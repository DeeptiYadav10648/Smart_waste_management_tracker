from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_socketio import SocketIO
from random import randint
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)
login_manager = LoginManager(app)

# Bin simulation
bins = [
    {"location": "Sector 1", "fillLevel": 60, "lat": 27.578, "lon": 77.696},
    {"location": "Sector 2", "fillLevel": 30, "lat": 27.580, "lon": 77.700}
]

users = {"user@example.com": {"password": "pass123", "tokens": 0}}

class User(UserMixin):
    def __init__(self, email): self.id = email

@login_manager.user_loader
def load_user(user_id): return User(user_id)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        if users.get(email) and users[email]['password'] == password:
            login_user(User(email))
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard(): return render_template('dashboard.html', user_id=session['_user_id'])

@app.route('/report_bin', methods=['POST'])
@login_required
def report_bin():
    users[session['_user_id']]['tokens'] += 10
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout(): logout_user(); return redirect('/login')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    print(f"Feedback: {data['feedback']}")
    return "Thanks!"

@app.route('/check_overflow')
def check_overflow():
    return jsonify([bin for bin in bins if bin['fillLevel'] >= 90])

@app.route('/nearby_bins', methods=['POST'])
def nearby_bins():
    data = request.get_json()
    lat, lon = data['lat'], data['lon']
    nearby = [bin for bin in bins if ((lat - bin['lat'])**2 + (lon - bin['lon'])**2)**0.5 < 0.01]
    return jsonify(nearby)

def simulate_bins():
    while True:
        for bin in bins:
            bin['fillLevel'] = max(0, min(100, bin['fillLevel'] + randint(-5, 10)))
        socketio.emit('bin_update', bins)
        time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=simulate_bins).start()
    socketio.run(app, debug=True)