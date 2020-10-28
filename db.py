from datetime import datetime
from bson.objectid import ObjectId
from user import User
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

try:
    client = MongoClient(
        'mongodb+srv://vedant:ved1357ved@cluster0.lkxqu.mongodb.net/<dbname>?retryWrites=true&w=majority')
    print('DB connection successful')

    chat_db = client.get_database('ChatDB')

    # collections
    users_collection = chat_db.get_collection('users')
    rooms_collection = chat_db.get_collection('rooms')
    room_members_collection = chat_db.get_collection('room_members')

    # ------------------------------- User Queries ------------------------------------

    # register user
    def register_user(username, password):
        user = users_collection.find_one({'username': username})
        if user:
            return 'User already exists'
        else:
            hashed_password = generate_password_hash(password)
            users_collection.insert_one({
                'username': username,
                'password': hashed_password
            })
            return 'success'

    # get user data
    def get_user(username):
        user_data = users_collection.find_one({'username': username})
        if user_data:
            return User(user_data['username'], user_data['password'])
        else:
            return None

    # ----------------------------- Room Queries ---------------------------------

    # create new room
    def create_room(room_name, created_by):
        room_id = rooms_collection.insert_one({
            'room_name': room_name,
            'created_by': created_by,
            'created_at': datetime.now(),
        }).inserted_id

        add_room_member(room_id, room_name, created_by,
                        created_by, is_room_admin=True)
        return room_id

    # get room by id
    def get_room(room_id):
        return rooms_collection.find_one({'_id': ObjectId(room_id)})

    # change room name
    def change_room_name(room_id, room_name):
        rooms_collection.update_one(
            {'_id': ObjectId(room_id)},
            {'$set': {'room_name': room_name}}
        )
        room_members_collection.update_many(
            {'_id.room_id': room_id},
            {'$set': {'room_name': room_name}}
        )

    # ------------------------------ Room member queries --------------------------------

    # add new member in a room
    def add_room_member(room_id, room_name, username, added_by, is_room_admin=False):
        room_members_collection.insert_one({
            '_id': {'username': username, 'room_id': ObjectId(room_id)},
            'room_name': room_name,
            'added_by': added_by,
            'added_at': datetime.now(),
            'is_room_admin': is_room_admin
        })

    # add room members in a room
    def add_room_members(room_id, room_name, usernames, added_by):
        room_members_collection.insert_many([
            {
                '_id': {'username': username, 'room_id': ObjectId(room_id)},
                'room_name': room_name,
                'added_by': added_by,
                'added_at': datetime.now(),
                'is_room_admin': False
            }
            for username in usernames
        ])

    # get room members by room id
    def get_room_members(room_id):
        return list(room_members_collection.find({'_id.room_id': ObjectId(room_id)}))

    # get rooms for user
    def get_rooms_for_user(username):
        return list(room_members_collection.find({'_id.username': username}))

    # check if user is room member
    def is_room_member(room_id, username):
        return room_members_collection.count_documents({
            '_id': {'username': username, 'room_id': ObjectId(room_id)}
        })

    # check if user is room admin of room
    def check_if_room_admin(room_id, username):
        print(room_id, username)
        return room_members_collection.count_documents({
            '_id.room_id': ObjectId(room_id),
            '_id.username': username,
            'is_room_admin': True
        })

    # remove room member
    def remove_room_members(room_id, usernames):
        room_members_collection.delete_many({
            '_id': {'$in': [{'room_id': ObjectId(room_id), 'username': username} for username in usernames]}
        })

except:
    print('Something went wrong in DB')
