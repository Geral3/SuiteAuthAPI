import bcrypt

from models.invite import Invite
from mongoHandler import get_db

class User:
    """
    User model with bcrypt hashing and user groups.
    Fields:
      username (str)
      password_hash (str)
      invited_by (str)
      invite_code (str)
      invites_remaining (int)
      invitees (list)
      user_group (str) - 'admin' or 'standard' (default)
    """

    def __init__(self, username, password_hash=None, invited_by=None, invite_code=None, invites_remaining=0, invitees=None, user_group='standard',_id=None):
        self.username = username
        self.password_hash = password_hash
        self.invited_by = invited_by
        self.invite_code = invite_code
        self.invites_remaining = invites_remaining
        self.invitees = invitees if invitees is not None else []
        self.user_group = user_group
        self._id = _id

    @classmethod
    def find_by_username(cls, username: str):
        """
        Find a user by username.
        :param username:
        :return:
        """
        db = get_db()
        user_data = db.users.find_one({'username': username})
        if user_data:
            return cls(
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                invited_by=user_data.get('invited_by'),
                invite_code=user_data.get('invite_code'),
                invites_remaining=user_data.get('invites_remaining', 0),
                invitees=user_data.get('invitees', []),
                user_group=user_data.get('user_group', 'standard'),
                _id=user_data['_id']
               )
        return None

    @classmethod
    def create_user(cls, username: str, password: str, invite_code: str):
        """
        Create a new user w\ hashed password.
        :param username:
        :param password:
        :return:
        """
        db = get_db()

        # Check if user already exists
        if cls.find_by_username(username) is not None:
            raise ValueError('User already exists')

        # Check if invite code is valid
        invite = Invite.find_by_code(invite_code)
        if invite is None:
            raise ValueError('Invalid invite code')

        if not invite.is_valid():
            raise ValueError('Invite code has expired')

        #bcrypt hash setup
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_str = hashed.decode('utf-8')

        invited_by = invite.created_by if invite.created_by is not None else None

        # Create user
        user_doc = {
            'username': username,
            'password_hash': hashed_str,
            'invited_by': invited_by,
            'invite_code': invite.code,
            'invites_remaining': 0,
            'invitees': [],
            'user_group': 'standard'
        }
        result = db.users.insert_one(user_doc)

        # Mark invite as used
        invite.mark_as_used(username)

        # If invited_by exists, add this user to the inviter's invitees array
        if invited_by:
            db.users.update_one(
                {'username': invited_by},
                {'$push': {'invitees': username}}
            )

        return cls(
            username=username,
            password_hash=hashed_str,
            invited_by=invited_by,
            invite_code=invite.code,
            invites_remaining=0,
            invitees=[],
            _id=result.inserted_id
        )

    def check_password(self, password: str):
        """
        Check if the provided password matches the stored hash.
        :param password:
        :return:
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))