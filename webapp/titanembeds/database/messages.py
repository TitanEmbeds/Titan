from titanembeds.database import db
from sqlalchemy import cast
import json

class Messages(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)                    # Auto incremented id
    guild_id = db.Column(db.String(255), nullable=False)            # Discord guild id
    channel_id = db.Column(db.String(255), nullable=False)          # Channel id
    message_id = db.Column(db.String(255), nullable=False)          # Message snowflake
    content = db.Column(db.Text(), nullable=False)                  # Message contents
    author = db.Column(db.Text(), nullable=False)                   # Author
    timestamp = db.Column(db.TIMESTAMP, nullable=False)             # Timestamp of when content is created
    edited_timestamp = db.Column(db.TIMESTAMP)                      # Timestamp of when content is edited
    mentions = db.Column(db.Text())                                 # Mentions serialized
    attachments = db.Column(db.Text())                              # serialized attachments

    def __init__(self, guild_id, channel_id, message_id, content, author, timestamp, edited_timestamp, mentions, attachments):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.content = content
        self.author = author
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp
        self.mentions = mentions
        self.attachments = attachments

    def __repr__(self):
        return '<Messages {0} {1} {2} {3} {4}>'.format(self.id, self.guild_id, self.guild_id, self.channel_id, self.message_id)

def get_channel_messages(channel_id, after_snowflake=None):
    if not after_snowflake:
        q = db.session.query(Messages).filter(Messages.channel_id == channel_id).order_by(Messages.id.desc()).limit(50)
    else:
        q = db.session.query(Messages).filter(cast(Messages.channel_id, db.Integer) == int(channel_id)).filter(Messages.message_id > after_snowflake).order_by(Messages.id.desc()).limit(50)
    msgs = []
    for x in q:
        msgs.append({
            "attachments": json.loads(x.attachments),
            "timestamp": x.timestamp,
            "id": x.message_id,
            "edited_timestamp": x.edited_timestamp,
            "author": json.loads(x.author),
            "content": x.content,
            "channel_id": x.channel_id,
            "mentions": json.loads(x.mentions)
        })
    return msgs
