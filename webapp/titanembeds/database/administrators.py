from titanembeds.database import db

class Administrators(db.Model):
    __tablename__ = "administrators"
    user_id = db.Column(db.BigInteger, nullable=False, primary_key=True)             # Discord user id of user of an administrator

def get_administrators_list():
    q = db.session.query(Administrators).all()
    their_ids = []
    for admin in q:
        their_ids.append(str(admin.user_id))
    return their_ids