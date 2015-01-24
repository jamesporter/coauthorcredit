from google.appengine.ext import db
import string
import random


def generate_code(size=64, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class UserRecord(db.Model):
    userId = db.StringProperty()
    email = db.EmailProperty()
    name = db.StringProperty()
    code = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get_and_create(cls, user):
        print "getting and creating", user
        """
        Returns a UserRecord for a user (i.e. users.get_current_user() type of user!)
        """
        us = UserRecord.gql("WHERE userId = :1", user.user_id())
        if us.count() > 0:
            return us[0]
        else:
            u = UserRecord()
            u.email = user.email()
            u.name = ""
            u.userId = user.user_id()
            u.code = generate_code()
            u.put()
            return u

    @classmethod
    def get_user(cls, user):
        us = UserRecord.gql("WHERE userId = :1", user.user_id())
        if us.count() > 0:
            return us[0]
        else:
            return None