from titanembeds.database import db

class Administrators(db.Model):
    __tablename__ = "administrators"
    id = db.Column(db.Integer, primary_key=True)                    # Auto increment id
    user_id = db.Column(db.String(255), nullable=False)             # Discord user id of user of an administrator

def get_administrators_list():
    q = db.session.query(Administrators).all()
    their_ids = []
    for admin in q:
        their_ids.append(admin.user_id)
    return their_ids