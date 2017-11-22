from titanembeds.database import db

class Patreon(db.Model):
    __tablename__ = "patreon"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False) # User ID from patreon
    total_synced = db.Column(db.Integer, nullable=False) # Total cents synced on our end
    
    def __init__(self, user_id, total_synced=0):
        self.user_id = user_id
        self.total_synced = total_synced
    
    def __repr__(self):
        return '<Patreon {0} {1} {2}>'.format(self.id, self.user_id, self.total_synced)