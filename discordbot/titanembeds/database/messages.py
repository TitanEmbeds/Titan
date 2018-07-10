from titanembeds.database import db

class Messages(db.Model):
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