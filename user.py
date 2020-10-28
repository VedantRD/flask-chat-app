from werkzeug.security import check_password_hash


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def is_authenticated():
        return True

    def is_active():
        return True

    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    def check_password(self, password):
        return check_password_hash(self.password, password)
