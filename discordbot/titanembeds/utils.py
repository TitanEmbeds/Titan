import discord

def get_message_author(message):
    author = message.author
    obj = {
        "username": author.name,
        "discriminator": author.discriminator,
        "bot": author.bot,
        "id": author.id,
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
            "id": author.id,
            "avatar": author.avatar
        })
    return ments

def get_webhooks_list(guild_webhooks):
    webhooks = []
    for webhook in guild_webhooks:
        webhooks.append({
            "id": webhook.id,
            "guild_id": webhook.server.id,
            "channel_id": webhook.channel.id,
            "name": webhook.name,
            "token": webhook.token,
        })
    return webhooks

def get_emojis_list(guildemojis):
    emojis = []
    for emote in guildemojis:
        emojis.append({
            "id": emote.id,
            "name": emote.name,
            "require_colons": emote.require_colons,
            "managed": emote.managed,
            "roles": list_role_ids(emote.roles),
            "url": emote.url
        })
    return emojis

def get_roles_list(guildroles):
    roles = []
    for role in guildroles:
        roles.append({
            "id": role.id,
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
        if str(channel.type) == "text":
            overwrites = []
            for target, overwrite in channel.overwrites:
                if isinstance(target, discord.Role):
                    type = "role"
                else:
                    type = "member"
                allow, deny = overwrite.pair()
                allow = allow.value
                deny = deny.value
                overwrites.append({
                    "id": target.id,
                    "type": type,
                    "allow": allow,
                    "deny": deny,
                })

            channels.append({
                "id": channel.id,
                "name": channel.name,
                "topic": channel.topic,
                "position": channel.position,
                "type": str(channel.type),
                "permission_overwrites": overwrites
            })
    return channels