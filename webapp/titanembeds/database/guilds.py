from titanembeds.database import db

class Guilds(db.Model):
    __tablename__ = "guilds"
    guild_id = db.Column(db.BigInteger, nullable=False, primary_key=True)       # Discord guild id
    unauth_users = db.Column(db.Boolean(), nullable=False, default=1)           # If allowed unauth users
    visitor_view = db.Column(db.Boolean(), nullable=False, default=0)           # If users are automatically "signed in" and can view chat
    webhook_messages = db.Column(db.Boolean(), nullable=False, default=0)       # Use webhooks to send messages instead of the bot
    guest_icon = db.Column(db.String(255), default=None)                        # Guest icon url, None if unset
    chat_links = db.Column(db.Boolean(), nullable=False, default=1)             # If users can post links
    bracket_links = db.Column(db.Boolean(), nullable=False, default=1)          # If appending brackets to links to prevent embed
    unauth_captcha = db.Column(db.Boolean(), nullable=False, server_default="1")# Enforce captcha on guest users
    mentions_limit = db.Column(db.Integer, nullable=False, default=11)          # If there is a limit on the number of mentions in a msg
    invite_link = db.Column(db.String(255))                                     # Custom Discord Invite Link
    post_timeout = db.Column(db.Integer, nullable=False, server_default="5")    # Seconds to elapse before another message can be posted from the widget
    max_message_length = db.Column(db.Integer, nullable=False, server_default="300") # Chars length the message should be before being rejected by the server
    banned_words_enabled = db.Column(db.Boolean(), nullable=False, server_default="0") # If banned words are enforced
    banned_words_global_included = db.Column(db.Boolean(), nullable=False, server_default="0") # Add global banned words to the list
    banned_words = db.Column(db.Text(), nullable=False, server_default="[]")    # JSON list of strings to block from sending
    autorole_unauth = db.Column(db.BigInteger, nullable=True, server_default=None) # Automatic Role inherit for unauthenticated users
    autorole_discord = db.Column(db.BigInteger, nullable=True, server_default=None) # Automatic Role inherit for discord users

    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.unauth_users = True # defaults to true
        self.visitor_view = False
        self.webhook_messages = False
        self.guest_icon = None
        self.chat_links = True
        self.bracket_links = True
        self.unauth_captcha = True
        self.mentions_limit = -1 # -1 = unlimited mentions

    def __repr__(self):
        return '<Guilds {0} {1}>'.format(self.id, self.guild_id)

    def set_unauthUsersBool(self, value):
        self.unauth_users = value
        return self.unauth_users
