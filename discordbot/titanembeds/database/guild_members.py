from titanembeds.database import db

class GuildMembers(db.Model):
    __tablename__ = "guild_members"
    id = db.Column(db.Integer, primary_key=True)    # Auto incremented id
    guild_id = db.Column(db.BigInteger)            # Discord guild id
    user_id = db.Column(db.BigInteger)             # Discord user id
    username = db.Column(db.String(255))            # Name
    discriminator = db.Column(db.Integer)           # User discriminator
    nickname = db.Column(db.String(255))            # User nickname
    avatar = db.Column(db.String(255))              # The avatar str of the user
    active = db.Column(db.Boolean())                # If the user is a member of the guild
    banned = db.Column(db.Boolean())                # If the user is banned in the guild
    roles = db.Column(db.Text())                    # Member roles