from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Data file paths
USERS_FILE = 'data/users.json'
NOTES_FILE = 'data/notes.json'
TODOS_FILE = 'data/todos.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, password_hash, email=None, created_at=None, profile=None, city=None):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = created_at
        self.profile = profile or {}
        self.city = city or 'Ankara'

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return User(
                user['id'], 
                user['username'], 
                user['password_hash'],
                user.get('email'),
                user.get('created_at'),
                user.get('profile', {}),
                user.get('city', 'Ankara')
            )
    return None

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('users', [])
    return []

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'users': users}, f, ensure_ascii=False, indent=4)

def load_notes():
    """Load notes from JSON file"""
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('notes', [])
    return []

def save_notes(notes):
    """Save notes to JSON file"""
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump({'notes': notes}, f, ensure_ascii=False, indent=4)

def load_todos():
    """Load todos from JSON file"""
    if os.path.exists(TODOS_FILE):
        with open(TODOS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('todos', [])
    return []

def save_todos(todos):
    """Save todos to JSON file"""
    with open(TODOS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'todos': todos}, f, ensure_ascii=False, indent=4)

def load_config():
    """Load configuration from JSON file"""
    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_weather_data(city=None):
    """Get weather data from OpenWeatherMap API"""
    try:
        # config = load_config()
        api_key = os.getenv('WEATHER_API_KEY')
        default_city = 'Ankara'
        
        print(f"=== Weather API Call ===")
        print(f"Requested city: {city}")
        print(f"Default city: {default_city}")
        
        if not api_key:
            print("No API key found")
            return None
        
        # Use provided city or default city
        target_city = city or default_city
        print(f"Target city: {target_city}")
        
        # API endpoint for current weather
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': target_city,
            'appid': api_key,
            'units': 'metric',  # Celsius
            'lang': 'tr'  # Turkish
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract weather information
            weather_info = {
                'city': data['name'],
                'temperature': round(data['main']['temp']),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'emoji': get_weather_emoji(data['weather'][0]['id'])
            }
            
            print(f"Weather data: {weather_info}")
            return weather_info
        else:
            print(f"API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Weather API exception: {e}")
        return None

def get_weather_emoji(weather_id):
    """Convert weather ID to emoji"""
    if weather_id >= 200 and weather_id < 300:
        return "⛈️"  # Thunderstorm
    elif weather_id >= 300 and weather_id < 400:
        return "🌧️"  # Drizzle
    elif weather_id >= 500 and weather_id < 600:
        return "🌧️"  # Rain
    elif weather_id >= 600 and weather_id < 700:
        return "❄️"  # Snow
    elif weather_id >= 700 and weather_id < 800:
        return "🌫️"  # Atmosphere (fog, mist, etc.)
    elif weather_id == 800:
        return "☀️"  # Clear sky
    elif weather_id == 801:
        return "🌤️"  # Few clouds
    elif weather_id == 802:
        return "⛅"  # Scattered clouds
    elif weather_id >= 803 and weather_id < 900:
        return "☁️"  # Broken clouds
    else:
        return "🌤️"  # Default

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember') == 'on'
        
        users = load_users()
        user = None
        
        for u in users:
            if u['username'] == username:
                user = u
                break
        
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(
                user['id'], 
                user['username'], 
                user['password_hash'],
                user.get('email'),
                user.get('created_at'),
                user.get('profile', {}),
                user.get('city', 'Ankara')
            )
            login_user(user_obj, remember=remember)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Geçersiz kullanıcı adı veya şifre')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    all_notes = load_notes()
    user_notes = []
    
    for note in all_notes:
        if note['user_id'] == current_user.id:
            # Eski notlar için varsayılan değerler ekle
            if 'category' not in note:
                note['category'] = 'Genel'
            if 'color' not in note:
                note['color'] = '#667eea'
            if 'tags' not in note:
                note['tags'] = []
            user_notes.append(note)
    
    # En son eklenen notu bul
    latest_note = None
    if user_notes:
        user_notes.sort(key=lambda x: x['created_at'], reverse=True)
        latest_note = user_notes[0]
    
    # Kullanıcının yapılacaklar listesini yükle
    all_todos = load_todos()
    user_todos = [todo for todo in all_todos if todo['user_id'] == current_user.id]
    
    # İstatistikler
    total_notes = len(user_notes)
    categories = set(note['category'] for note in user_notes)
    categories_count = len(categories)
    total_todos = len(user_todos)
    completed_todos = len([todo for todo in user_todos if todo['completed']])
    
    # Hava durumu verilerini al (kullanıcının şehrine göre)
    user_city = getattr(current_user, 'city', 'Ankara') or 'Ankara'
    weather_data = get_weather_data(user_city)
    
    return render_template('dashboard.html', 
                         latest_note=latest_note,
                         total_notes=total_notes,
                         categories_count=categories_count,
                         todos=user_todos,
                         total_todos=total_todos,
                         completed_todos=completed_todos,
                         weather=weather_data)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        city = request.form.get('city', 'Ankara')
        
        if password != confirm_password:
            return render_template('register.html', error='Şifreler eşleşmiyor')
        
        if not city:
            return render_template('register.html', error='Lütfen bir şehir seçin')
        
        users = load_users()
        
        # Check if username already exists
        for user in users:
            if user['username'] == username:
                return render_template('register.html', error='Bu kullanıcı adı zaten kullanılıyor')
        
        # Create new user
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password_hash': generate_password_hash(password),
            'email': '',
            'city': city,
            'created_at': datetime.now().isoformat(),
            'profile': {
                'display_name': username,
                'bio': '',
                'theme': 'light'
            }
        }
        
        users.append(new_user)
        save_users(users)
        
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/notes')
@login_required
def notes():
    all_notes = load_notes()
    user_notes = []
    
    for note in all_notes:
        if note['user_id'] == current_user.id:
            # Eski notlar için varsayılan değerler ekle
            if 'category' not in note:
                note['category'] = 'Genel'
            if 'color' not in note:
                note['color'] = '#667eea'
            if 'tags' not in note:
                note['tags'] = []
            user_notes.append(note)
    
    # Arama filtresi
    search_query = request.args.get('search', '').strip()
    if search_query:
        user_notes = [note for note in user_notes if 
                     search_query.lower() in note['title'].lower() or 
                     search_query.lower() in note['content'].lower()]
    
    # Sıralama
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'newest':
        user_notes.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == 'oldest':
        user_notes.sort(key=lambda x: x['created_at'])
    
    # Hava durumu verilerini al (kullanıcının şehrine göre)
    user_city = getattr(current_user, 'city', 'Ankara') or 'Ankara'
    weather_data = get_weather_data(user_city)
    
    return render_template('notlar.html', 
                         notes=user_notes, 
                         search_query=search_query, 
                         sort_by=sort_by,
                         weather=weather_data)

@app.route('/add_note', methods=['POST'])
@login_required
def add_note():
    title = request.form['title']
    content = request.form['content']
    category = request.form.get('category', 'Genel')
    color = request.form.get('color', '#667eea')
    tags_input = request.form.get('tags', '')
    
    if not title or not content:
        flash('Başlık ve içerik gereklidir')
        return redirect(url_for('notes'))
    
    # Etiketleri işle
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    
    new_note = {
        'id': str(uuid.uuid4()),
        'user_id': current_user.id,
        'title': title,
        'content': content,
        'category': category,
        'color': color,
        'tags': tags,
        'created_at': datetime.now().isoformat()
    }
    
    notes = load_notes()
    notes.append(new_note)
    save_notes(notes)
    
    return redirect(url_for('notes'))

@app.route('/edit_note/<note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    notes = load_notes()
    note = None
    
    # Notu bul ve kullanıcıya ait olduğunu kontrol et
    for n in notes:
        if n['id'] == note_id and n['user_id'] == current_user.id:
            note = n
            break
    
    if not note:
        flash('Not bulunamadı veya bu notu düzenleme yetkiniz yok')
        return redirect(url_for('notes'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form.get('category', 'Genel')
        color = request.form.get('color', '#667eea')
        tags_input = request.form.get('tags', '')
        
        if not title or not content:
            flash('Başlık ve içerik gereklidir')
            return render_template('edit_note.html', note=note)
        
        # Etiketleri işle
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Notu güncelle
        note['title'] = title
        note['content'] = content
        note['category'] = category
        note['color'] = color
        note['tags'] = tags
        
        save_notes(notes)
        flash('Not başarıyla güncellendi!')
        return redirect(url_for('notes'))
    
    return render_template('edit_note.html', note=note)

@app.route('/delete_note/<note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    notes = load_notes()
    
    # Find and remove the note if it belongs to the current user
    for i, note in enumerate(notes):
        if note['id'] == note_id and note['user_id'] == current_user.id:
            del notes[i]
            save_notes(notes)
            break
    
    return redirect(url_for('notes'))

@app.route('/profile')
@login_required
def profile():
    users = load_users()
    user_data = None
    
    for user in users:
        if user['id'] == current_user.id:
            user_data = user
            break
    
    return render_template('profile.html', user=user_data)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    display_name = request.form.get('display_name', '')
    bio = request.form.get('bio', '')
    theme = request.form.get('theme', 'light')
    city = request.form.get('city', 'Ankara')
    
    users = load_users()
    
    for user in users:
        if user['id'] == current_user.id:
            if 'profile' not in user:
                user['profile'] = {}
            user['profile']['display_name'] = display_name
            user['profile']['bio'] = bio
            user['profile']['theme'] = theme
            user['city'] = city
            break
    
    save_users(users)
    flash('Profil başarıyla güncellendi!')
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        
        # Yeni şifreler eşleşiyor mu kontrol et
        if new_password != confirm_new_password:
            return render_template('change_password.html', error='Yeni şifreler eşleşmiyor')
        
        # Mevcut şifreyi kontrol et
        users = load_users()
        user = None
        
        for u in users:
            if u['id'] == current_user.id:
                user = u
                break
        
        if not user or not check_password_hash(user['password_hash'], current_password):
            return render_template('change_password.html', error='Mevcut şifre yanlış')
        
        # Şifreyi güncelle
        user['password_hash'] = generate_password_hash(new_password)
        save_users(users)
        
        return render_template('change_password.html', success='Şifreniz başarıyla değiştirildi!')
    
    return render_template('change_password.html')

@app.route('/toggle_theme')
@login_required
def toggle_theme():
    users = load_users()
    
    for user in users:
        if user['id'] == current_user.id:
            if 'profile' not in user:
                user['profile'] = {}
            current_theme = user['profile'].get('theme', 'light')
            new_theme = 'dark' if current_theme == 'light' else 'light'
            user['profile']['theme'] = new_theme
            break
    
    save_users(users)
    return redirect(request.referrer or url_for('notes'))

@app.route('/test_weather')
def test_weather():
    """Test weather API endpoint"""
    weather_data = get_weather_data()
    if weather_data:
        return jsonify({
            'success': True,
            'weather': weather_data
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Weather data could not be retrieved'
        })

# Todo routes
@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    task = request.form.get('task', '').strip()
    
    if not task:
        flash('Görev metni gereklidir')
        return redirect(url_for('dashboard'))
    
    new_todo = {
        'id': str(uuid.uuid4()),
        'user_id': current_user.id,
        'task': task,
        'completed': False,
        'created_at': datetime.now().isoformat()
    }
    
    todos = load_todos()
    todos.append(new_todo)
    save_todos(todos)
    
    return redirect(url_for('dashboard'))

@app.route('/toggle_todo/<todo_id>', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    todos = load_todos()
    
    for todo in todos:
        if todo['id'] == todo_id and todo['user_id'] == current_user.id:
            todo['completed'] = not todo['completed']
            break
    
    save_todos(todos)
    return redirect(url_for('dashboard'))

@app.route('/delete_todo/<todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todos = load_todos()
    
    # Find and remove the todo if it belongs to the current user
    for i, todo in enumerate(todos):
        if todo['id'] == todo_id and todo['user_id'] == current_user.id:
            del todos[i]
            break
    
    save_todos(todos)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
