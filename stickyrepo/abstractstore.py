class AbstractStore(object):

    def delete_user(self, username):
        raise NotImplemented

    def user_last_updated(self, username):
        raise NotImplemented

    def user_data(self, username):
        raise NotImplemented

    def update_user_data(self, username, new_data):
        raise NotImplemented
