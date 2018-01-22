from titanembeds.database import db
import json

class Cosmetics(db.Model):
    __tablename__ = "cosmetics"
    id = db.Column(db.Integer, primary_key=True)                    # Auto increment id
    user_id = db.Column(db.String(255), nullable=False)             # Discord user id of user of cosmetics
    css = db.Column(db.Boolean(), nullable=False)                   # If they can create/edit custom CSS
    css_limit = db.Column(db.Integer, nullable=False, server_default="0") # Custom CSS Limit
    guest_icon = db.Column(db.Boolean(), nullable=False, server_default=db.false()) # If they can set the guest icon for all guilds
    badges = db.Column(db.String(255), nullable=False, server_default="[]") # JSON list of all the badges the user has
    
    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        
        if "css" in kwargs:
            self.css = kwargs["css"]
        else:
            self.css = False
        
        if "css_limit" in kwargs:
            self.css_limit = kwargs["css_limit"]
        else:
            self.css_limit = 0

        if "guest_icon" in kwargs:
            self.guest_icon = kwargs["guest_icon"]
        else:
            self.guest_icon = False
        
        if "badges" in kwargs:
            self.badges = json.dumps(kwargs["badges"])
        else:
            self.badges = "[]"

def set_badges(user_id, badges):
    usr = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if not usr:
        usr = Cosmetics(user_id)
    usr.badges = json.dumps(badges)
    db.session.add(usr)

def get_badges(user_id):
    usr = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if usr:
        return json.loads(usr.badges)
    return []

def add_badge(user_id, name):
    bgs = get_badges(user_id)
    if name not in bgs:
        bgs.append(name)
        set_badges(user_id, bgs)

def remove_badge(user_id, name):
    bgs = get_badges(user_id)
    if name in bgs:
        bgs.remove(name)
        set_badges(user_id, bgs)