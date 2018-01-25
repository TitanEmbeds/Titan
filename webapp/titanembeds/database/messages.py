from titanembeds.database import db, get_guild_member
from sqlalchemy import cast
import json

class Messages(db.Model):
    __tablename__ = "messages"
    message_id = db.Column(db.BigInteger, nullable=False, primary_key=True) # Message snowflake
    guild_id = db.Column(db.BigInteger, nullable=False)            # Discord guild id
    channel_id = db.Column(db.BigInteger, nullable=False)          # Channel id
    content = db.Column(db.Text(), nullable=False)                  # Message contents
    author = db.Column(db.Text(), nullable=False)                   # Author
    timestamp = db.Column(db.TIMESTAMP, nullable=False)             # Timestamp of when content is created
    edited_timestamp = db.Column(db.TIMESTAMP)                      # Timestamp of when content is edited
    mentions = db.Column(db.Text())                                 # Mentions serialized
    attachments = db.Column(db.Text())                              # serialized attachments
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

def get_channel_messages(guild_id, channel_id, after_snowflake=None):
    if not after_snowflake:
        q = db.session.query(Messages).filter(Messages.channel_id == channel_id).order_by(Messages.timestamp.desc()).limit(50)
    else:
        q = db.session.query(Messages).filter(Messages.channel_id == channel_id).filter(Messages.message_id > after_snowflake).order_by(Messages.timestamp.desc()).limit(50)
    msgs = []
    snowflakes = []
    guild_members = {}
    for x in q:
        if x.message_id in snowflakes:
            continue
        snowflakes.append(x.message_id)
        embeds = x.embeds
        if not embeds:
            embeds = "[]"
        message = {
            "attachments": json.loads(x.attachments),
            "timestamp": x.timestamp,
            "id": str(x.message_id),
            "edited_timestamp": x.edited_timestamp,
            "author": json.loads(x.author),
            "content": x.content,
            "channel_id": str(x.channel_id),
            "mentions": json.loads(x.mentions),
            "embeds": json.loads(embeds),
        }
        if message["author"]["id"] not in guild_members:
            member = get_guild_member(guild_id, message["author"]["id"])
            guild_members[message["author"]["id"]] = member
        else:
            member = guild_members[message["author"]["id"]]
        message["author"]["nickname"] = None
        if member:
            message["author"]["nickname"] = member.nickname
            message["author"]["avatar"] = member.avatar
            message["author"]["discriminator"] = member.discriminator
            message["author"]["username"] = member.username
        for mention in message["mentions"]:
            if mention["id"] not in guild_members:
                author = get_guild_member(guild_id, mention["id"])
                guild_members[mention["id"]] = author
            else:
                author = guild_members[mention["id"]]
            mention["nickname"] = None
            if author:
                mention["nickname"] = author.nickname
                mention["avatar"] = author.avatar
                mention["username"] = author.username
                mention["discriminator"] = author.discriminator
        msgs.append(message)
    return msgs
