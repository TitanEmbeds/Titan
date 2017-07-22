from titanembeds.database import db

class Cosmetics(db.Model):
    __tablename__ = "cosmetics"
    id = db.Column(db.Integer, primary_key=True)                    # Auto increment id
    user_id = db.Column(db.String(255), nullable=False)             # Discord user id of user of cosmetics
    css = db.Column(db.Boolean(), nullable=False)                   # If they can create/edit custom CSS
    
    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        
        if "css" in kwargs:
            self.css = kwargs["css"]
        else:
            self.css = False
