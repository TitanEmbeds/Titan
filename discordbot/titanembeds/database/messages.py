from titanembeds.database import db, Base

class Messages(Base):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)    # Auto incremented id
    guild_id = db.Column(db.String(255))            # Discord guild id
    channel_id = db.Column(db.String(255))          # Channel id
    message_id = db.Column(db.String(255))          # Message snowflake
    content = db.Column(db.Text())                  # Message contents
    timestamp = db.Column(db.TIMESTAMP)             # Timestamp of when content is created
    edited_timestamp = db.Column(db.TIMESTAMP)      # Timestamp of when content is edited
    mentions = db.Column(db.Text())                 # Mentions serialized
    attachments = db.Column(db.Text())              # serialized attachments

    def __init__(self, guild_id, channel_id, message_id, content, timestamp, edited_timestamp, mentions, attachments):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.content = content
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp
        self.mentions = mentions
        self.attachments = attachments

    def __repr__(self):
        return '<Messages {0} {1} {2} {3} {4}>'.format(self.id, self.guild_id, self.guild_id, self.channel_id, self.message_id)
