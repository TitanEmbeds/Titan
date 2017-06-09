from titanembeds.database import db

class Guilds(db.Model):
    __tablename__ = "guilds"
    id = db.Column(db.Integer, primary_key=True)                                # Auto incremented id
    guild_id = db.Column(db.String(255), nullable=False)                        # Discord guild id
    name = db.Column(db.String(255), nullable=False)                            # Name
    unauth_users = db.Column(db.Boolean(), nullable=False, default=1)           # If allowed unauth users
    visitor_view = db.Column(db.Boolean(), nullable=False, default=0)           # If users are automatically "signed in" and can view chat
    chat_links = db.Column(db.Boolean(), nullable=False, default=1)             # If users can post links
    bracket_links = db.Column(db.Boolean(), nullable=False, default=1)          # If appending brackets to links to prevent embed
    mentions_limit = db.Column(db.Integer, nullable=False, default=11)          # If there is a limit on the number of mentions in a msg
    roles = db.Column(db.Text(), nullable=False)                                # Guild Roles
    channels = db.Column(db.Text(), nullable=False)                             # Guild channels
    emojis = db.Column(db.Text(), nullable=False)                               # Guild Emojis
    owner_id = db.Column(db.String(255), nullable=False)                        # Snowflake of the owner
    icon = db.Column(db.String(255))                                            # The icon string, null if none
    discordio = db.Column(db.String(255))                                       # Custom Discord.io Invite Link

    def __init__(self, guild_id, name, roles, channels, emojis, owner_id, icon):
        self.guild_id = guild_id
        self.name = name
        self.unauth_users = True # defaults to true
        self.visitor_view = False
        self.chat_links = True
        self.bracket_links = True
        self.mentions_limit = -1 # -1 = unlimited mentions
        self.roles = roles
        self.channels = channels
        self.emojis = emojis
        self.owner_id = owner_id
        self.icon = icon

    def __repr__(self):
        return '<Guilds {0} {1}>'.format(self.id, self.guild_id)

    def set_unauthUsersBool(self, value):
        self.unauth_users = value
        db.session.commit()
        return self.unauth_users
