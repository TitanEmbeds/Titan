from titanembeds.database import db

class Guilds(db.Model):
    __tablename__ = "guilds"
    id = db.Column(db.Integer, primary_key=True)    # Auto incremented id
    guild_id = db.Column(db.String(255))            # Discord guild id
    unauth_users = db.Column(db.Boolean())          # If allowed unauth users

    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.unauth_users = true # defaults to true

    def __repr__(self):
        return '<Guilds {0} {1}>'.format(self.id, self.guild_id)

    def set_unauthUsersBool(self, value):
        self.unauth_users = value
        db.session.commit()
        return self.unauth_users
