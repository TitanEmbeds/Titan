from titanembeds.database import db

class Guilds(db.Model):
    __tablename__ = "guilds"
    id = db.Column(db.Integer, primary_key=True)    # Auto incremented id
    guild_id = db.Column(db.String(255))            # Discord guild id
    name = db.Column(db.String(255))                # Name
    unauth_users = db.Column(db.Boolean())          # If allowed unauth users
    roles = db.Column(db.Text())                    # Guild Roles
    channels = db.Column(db.Text())                 # Guild channels
    owner_id = db.Column(db.String(255))            # Snowflake of the owner
    icon = db.Column(db.String(255))                # The icon string, null if none

    def __init__(self, guild_id, name, roles, channels, owner_id, icon):
        self.guild_id = guild_id
        self.name = name
        self.unauth_users = True # defaults to true
        self.roles = roles
        self.channels = channels
        self.owner_id = owner_id
        self.icon = icon

    def __repr__(self):
        return '<Guilds {0} {1}>'.format(self.id, self.guild_id)

    def set_unauthUsersBool(self, value):
        self.unauth_users = value
        db.session.commit()
        return self.unauth_users
