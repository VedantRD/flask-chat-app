from flask_login.utils import login_required, login_user, logout_user, current_user
from db import change_room_name, check_if_room_admin, get_room, get_room_members, get_rooms_for_user, get_user, is_room_member, register_user, create_room, add_room_members, remove_room_members
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = 'my_secret_key'
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# -------------------------- User Auth Routes -------------------------------


# Landing route
@app.route('/')
def home():
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
        return render_template('join_room.html', rooms=rooms)
    else:
        return redirect(url_for('login'))


# login user
@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    login_message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user(username)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            login_message = 'Login Failed'
        return render_template('login.html', login_message=login_message)
    else:
        return render_template('login.html')


# register new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_message = ''
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            register_message = register_user(username, password)
            if register_message == 'success':
                user = get_user(username)
                login_user(user)
                return redirect(url_for('home'))
        else:
            register_message = 'All fields are required'
        return render_template('register.html', register_message=register_message)


# logout user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --------------------------- Room Routes --------------------------------


# create new room
@app.route('/create_room', methods=['GET', 'POST'])
@login_required
def create_new_room():
    create_room_message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [
            username.strip() for username in request.form.get('members').split(',')
        ]
        if len(room_name) and len(usernames):
            room_id = create_room(room_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            add_room_members(
                room_id, room_name, usernames, current_user.username
            )
            return redirect(url_for('home'))
        else:
            create_room_message = 'Failed to create room'
    return render_template('create_room.html', create_room_message=create_room_message)


# view room
@app.route('/rooms/<room_id>')
@login_required
def chat(room_id):
    room = get_room(room_id)
    room_members = get_room_members(room_id)
    if room and is_room_member(room_id, current_user.username):
        is_room_admin = check_if_room_admin(room_id, current_user.username)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members, is_room_admin=is_room_admin)
    else:
        return redirect(url_for('home'))


# edit room info
@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    room_members = [
        member['_id']['username'] for member in get_room_members(room_id)
    ]
    print('room members are ==', room_members)
    is_room_admin = check_if_room_admin(room_id, current_user.username)

    if request.method == 'POST':

        new_room_name = request.form.get('new_room_name')
        change_room_name(room_id, new_room_name)
        room['room_name'] = new_room_name

        new_room_members = [
            username.strip() for username in request.form.get('members').split(',')
        ]

        members_to_add = list(set(new_room_members) - set(room_members))
        members_to_remove = list(set(room_members) - set(new_room_members))

        if members_to_add:
            add_room_members(
                room_id, new_room_name, members_to_add, current_user.username
            )
        if members_to_remove:
            remove_room_members(room_id, members_to_remove)

        room_members = get_room_members(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members, is_room_admin=is_room_admin)

    else:
        room_members = ','.join(room_members)
        if room and is_room_member(room_id, current_user.username):
            return render_template('edit_room.html', username=current_user.username, room=room, room_members=room_members)
        else:
            return redirect(url_for('home'))


# -------------------------- Socket Events -------------------------------


# join room event
@socketio.on('join_room')
def handle_join_room(data):
    app.logger.info('{} has joined the room {}'.format(
        data['username'], data['room_id']))
    socketio.emit('join_room_announcement', data)


# send message event
@socketio.on('send_message')
def handle_send_message(data):
    data['username'] = current_user.username
    socketio.emit('receive_message', data)


# -------------------------- Handle Session -------------------------------


# user session
@login_manager.user_loader
def load_user(username):
    return get_user(username)


# -------------------------- Run the App -------------------------------

if __name__ == "__main__":
    socketio.run(app, debug=True)
