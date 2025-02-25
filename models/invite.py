from datetime import datetime, timedelta
from mongoHandler import get_db
import random

class Invite:
    """
    Represents an invite code stored in the 'invites' collection
    Fields:
        code: str
        expires_at: datetime
        created_at: datetime
        used: bool
        used_by: str
        created_by: str
    """

    def __init__(self, code, expires_at, created_at=datetime.now(), used=False, used_by=None, created_by=None, _id=None):
        self.code = code
        self.expires_at = expires_at
        self.created_at = created_at
        self.used = used
        self.used_by = used_by
        self.created_by = created_by
        self._id = _id

    @classmethod
    def find_by_code(cls, code: str):
        """
        Find an invite by code.
        :param code:
        :return:
        """
        db = get_db()
        invite_data = db.invites.find_one({'code': code})
        if invite_data:
            return cls(code=invite_data['code'],
                       expires_at=invite_data['expires_at'],
                       created_at=invite_data['created_at'],
                       used=invite_data['used'],
                       used_by=invite_data['used_by'],
                       created_by=invite_data['created_by'],
                       _id=invite_data['_id'])
        return None

    def is_valid(self) -> bool:
        """
        Check if the invite is valid.
        :return:
        """
        return not self.used and datetime.now() < self.expires_at

    def mark_as_used(self, used_by: str):
        """
        Mark the invite as used by a user.
        :param used_by:
        :return:
        """
        db = get_db()
        db.invites.update_one(
            {'_id': self._id},
            {'$set': {'used': True, 'used_by': used_by}}
        )

    @classmethod
    def create_invite(cls, expires_in_minutes: int, created_by: str):
        """
        Create a new invite code.
        :param expires_in_minutes:
        :param created_by:
        :return:
        """
        db = get_db()
        from models.user import User
        created_by = User.find_by_username(created_by)

        # Set the expiration date
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)

        # Generate a random code
        code = cls.gen_random_code()

        result = db.invites.insert_one({
            'code': code,
            'expires_at': expires_at,
            'created_at': datetime.now(),
            'used': False,
            'used_by': None,
            'created_by': created_by.username
        })

        if created_by.user_group == 'standard':
            db.users.update_one(
                {"_id": created_by._id},
                {"$inc": {"invites_remaining": -1}}
            )
            created_by.invites_remaining -= 1  # update in-memory object as well

        return cls(code=code, expires_at=expires_at, created_by=created_by.username, _id=result.inserted_id)


    def gen_random_code(self) -> str:
        """
        Generate a random 14 character code and ensure it is unique.
        :return:
        """

        code = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        while self.find_by_code(code):
            code = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))

        return code