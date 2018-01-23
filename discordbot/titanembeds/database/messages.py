from titanembeds.database import db, Base

class Messages(Base):
    __tablename__ = "messages"
    message_id = db.Column(db.BigInteger, primary_key=True)          # Message snowflake
    guild_id = db.Column(db.BigInteger)            # Discord guild id
    channel_id = db.Column(db.BigInteger)          # Channel id
    content = db.Column(db.Text())                  # Message contents
    author = db.Column(db.Text())                   # Author json
    timestamp = db.Column(db.TIMESTAMP)             # Timestamp of when content is created
    edited_timestamp = db.Column(db.TIMESTAMP)      # Timestamp of when content is edited
    mentions = db.Column(db.Text())                 # Mentions serialized
    attachments = db.Column(db.Text())              # serialized attachments
    embeds = db.Column(db.Text().with_variant(db.Text(length=4294967295), 'mysql')) # message embeds

    def __init__(self, guild_id, channel_id, message_id, content, author, timestamp, edited_timestamp, mentions, attachments, embeds):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.content = content
        self.author = author
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp
        self.mentions = mentions
        self.attachments = attachments
        self.embeds = embeds

    def __repr__(self):
        return '<Messages {0} {1} {2} {3} {4}>'.format(self.id, self.guild_id, self.guild_id, self.channel_id, self.message_id)
