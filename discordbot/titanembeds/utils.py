import discord
import time
from email import utils as emailutils

def format_datetime(datetimeobj):
    return emailutils.formatdate(time.mktime(datetimeobj.timetuple())) # https://stackoverflow.com/questions/3453177/convert-python-datetime-to-rfc-2822

def get_formatted_message(message):
    edit_ts = message.edited_at
    if not edit_ts:
        edit_ts = None
    else:
        edit_ts = format_datetime(edit_ts)
    msg_type = message.type
    if isinstance(msg_type, int):
        msg_type = int(msg_type)
    else:
        msg_type = message.type.value
    msg = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "content": message.content,
        "author": get_message_author(message),
        "timestamp": format_datetime(message.created_at),
        "edited_timestamp": edit_ts,
        "type": msg_type,
    }
    if hasattr(message, "mentions"):
        msg["mentions"] = get_message_mentions(message.mentions)
    if hasattr(message, "attachments"):
        msg["attachments"] = get_attachments_list(message.attachments)
    if hasattr(message, "embeds"):
        msg["embeds"] = get_embeds_list(message.embeds)
    if hasattr(message, "author"):
        nickname = None
        if hasattr(message.author, 'nick') and message.author.nick:
            nickname = message.author.nick
        msg["author"]["nickname"] = nickname
    if hasattr(message, "mentions"):
        for mention in msg["mentions"]:
            mention["nickname"] = None
            member = message.guild.get_member(mention["id"])
            if member:
                mention["nickname"] = member.nick
    if hasattr(message, "reactions"):
        msg["reactions"] = get_message_reactions(message.reactions)
    return msg

def get_formatted_user(user):
    userobj = {
        "avatar": user.avatar,
        "avatar_url": str(user.avatar_url_as(static_format="png", size=512)),
        "color": str(user.color)[1:],
        "discriminator": user.discriminator,
        "game": None,
        "hoist-role": None,
        "id": str(user.id),
        "status": str(user.status),
        "username": user.name,
        "nick": None,
        "bot": user.bot,
        "roles": []
    }
    if userobj["color"] == "000000":
        userobj["color"] = None
    # if userobj["avatar_url"][len(userobj["avatar_url"])-15:] != ".jpg":
    #     userobj["avatar_url"] = userobj["avatar_url"][:len(userobj["avatar_url"])-14] + ".jpg"
    if user.nick:
        userobj["nick"] = user.nick
    if hasattr(user, "activity") and user.activity:
        userobj["activity"] = {
            "name": user.activity.name
        }
    roles = sorted(user.roles, key=lambda k: k.position, reverse=True)
    for role in roles:
        userobj["roles"].append(str(role.id))
        if role.hoist and userobj["hoist-role"] == None:
            userobj["hoist-role"] = {
                "id": str(role.id),
                "name": role.name,
                "position": role.position,
            }
    return userobj

def get_message_author(message):
    if not hasattr(message, "author"):
        return {}
    author = message.author
    obj = {
        "username": author.name,
        "discriminator": author.discriminator,
        "bot": author.bot,
        "id": str(author.id),
        "avatar": author.avatar
    }
    return obj
    
def get_formatted_emojis(emojis):
    emotes = []
    for emo in emojis:
        emotes.append({
            "id": str(emo.id),
            "managed": emo.managed,
            "name": emo.name,
            "require_colons": emo.require_colons,
            "roles": get_roles_list(emo.roles),
            "url": str(emo.url),
        })
    return emotes

def get_formatted_guild(guild, webhooks=[]):
    guil = {
        "id": str(guild.id),
        "name": guild.name,
        "icon": guild.icon,
        "icon_url": str(guild.icon_url),
        "owner_id": guild.owner_id,
        "roles": get_roles_list(guild.roles),
        "channels": get_channels_list(guild.channels),
        "webhooks": get_webhooks_list(webhooks),
        "emojis": get_emojis_list(guild.emojis)
    }
    return guil

def get_formatted_channel(channel):
    chan = {
        "id": str(channel.id),
        "guild_id": str(channel.guild.id),
    }
    return chan

def get_formatted_role(role):
    rol = {
        "id": str(role.id),
        "guild_id": str(role.guild.id),
        "name": role.name,
        "color": role.color.value,
        "hoist": role.hoist,
        "position": role.position,
        "permissions": role.permissions.value,
    }
    return rol

def get_message_mentions(mentions):
    ments = []
    for author in mentions:
        ments.append({
            "username": author.name,
            "discriminator": author.discriminator,
            "bot": author.bot,
            "id": str(author.id),
            "avatar": author.avatar
        })
    return ments

def get_webhooks_list(guild_webhooks):
    webhooks = []
    for webhook in guild_webhooks:
        if not webhook.channel or not webhook.guild:
            continue
        webhooks.append({
            "id": str(webhook.id),
            "guild_id": str(webhook.guild.id),
            "channel_id": str(webhook.channel.id),
            "name": webhook.name,
            "token": webhook.token,
        })
    return webhooks

def get_emojis_list(guildemojis):
    emojis = []
    for emote in guildemojis:
        emojis.append({
            "id": str(emote.id),
            "name": emote.name,
            "require_colons": emote.require_colons,
            "managed": emote.managed,
            "roles": list_role_ids(emote.roles),
            "url": str(emote.url),
            "animated": emote.animated
        })
    return emojis

def get_roles_list(guildroles):
    roles = []
    for role in guildroles:
        roles.append({
            "id": str(role.id),
            "name": role.name,
            "color": role.color.value,
            "hoist": role.hoist,
            "position": role.position,
            "permissions": role.permissions.value
        })
    return roles

def get_channels_list(guildchannels):
    channels = []
    for channel in guildchannels:
        if isinstance(channel, discord.channel.TextChannel) or isinstance(channel, discord.channel.CategoryChannel):
            overwrites = []
            isTextChannel = isinstance(channel, discord.channel.TextChannel)
            for target, overwrite in channel.overwrites.items():
                if not target:
                    continue
                if isinstance(target, discord.Role):
                    type = "role"
                else:
                    type = "member"
                allow, deny = overwrite.pair()
                allow = allow.value
                deny = deny.value
                overwrites.append({
                    "id": str(target.id),
                    "type": type,
                    "allow": allow,
                    "deny": deny,
                })
            parent = channel.category
            if parent:
                parent = str(parent.id)
            channels.append({
                "id": str(channel.id),
                "name": channel.name,
                "topic": channel.topic if isTextChannel else None,
                "position": channel.position,
                "type": "text" if isTextChannel else "category",
                "permission_overwrites": overwrites,
                "parent_id": parent,
                "nsfw": channel.is_nsfw(),
            })
    return channels
    
def list_role_ids(usr_roles):
    ids = []
    for role in usr_roles:
        ids.append(str(role.id))
    return ids

def get_attachments_list(attachments):
    attr = []
    for attach in attachments:
        a = {
            "id": str(attach.id),
            "size": attach.size,
            "filename": attach.filename,
            "url": attach.url,
            "proxy_url": attach.proxy_url,
        }
        if attach.height:
            a["height"] = attach.height
        if attach.width:
            a["width"] = attach.width
        attr.append(a)
    return attr

def get_embeds_list(embeds):
    em = []
    for e in embeds:
        em.append(e.to_dict())
    return em

def get_message_reactions(reactions):
    reacts = []
    for reaction in reactions:
        reacts.append({
            "emoji": get_partial_emoji(reaction.emoji),
            "count": reaction.count
        })
    return reacts

def get_partial_emoji(emoji):
    emote = {
        "animated": False,
        "id": None,
        "name": str(emoji)
    }
    if isinstance(emoji, str):
        return emote
    emote["animated"] = emoji.animated
    emote["id"] = str(emoji.id)
    emote["name"] = emoji.name
    return emote