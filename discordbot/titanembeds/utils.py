import discord

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
            "url": emote.url,
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
            for target, overwrite in channel.overwrites:
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