from titanembeds.database import db

class Cosmetics(db.Model):
    __tablename__ = "cosmetics"
    id = db.Column(db.Integer, primary_key=True)    # Auto increment id
    user_id = db.Column(db.String(255))             # Discord user id of user of cosmetics
    css = db.Column(db.Boolean())                   # If they can create/edit custom CSS