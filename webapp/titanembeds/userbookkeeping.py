from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, AuthenticatedUsers, GuildMembers, get_guild_member
from titanembeds.utils import guild_accepts_visitors, guild_query_unauth_users_bool, get_client_ipaddr
from titanembeds.oauth import check_user_can_administrate_guild, user_has_permission
from flask import session
from sqlalchemy import and_
import json

def user_unauthenticated():
    if 'unauthenticated' in session:
        return session['unauthenticated']
    return True

def checkUserRevoke(guild_id, user_key=None):
    revoked = True #guilty until proven not revoked
    if user_unauthenticated():
        dbUser = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key).first()
        revoked = dbUser.isRevoked()
    else:
        banned = checkUserBanned(guild_id)
        if banned:
            return revoked
        dbUser = GuildMembers.query.filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == session["user_id"]).first()
        revoked = not dbUser or not dbUser.active
    return revoked

def checkUserBanned(guild_id, ip_address=None):
    banned = True
    if user_unauthenticated():
        dbUser = UnauthenticatedBans.query.filter(and_(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == ip_address)).all()
        if not dbUser:
            banned = False
        else:
            for usr in dbUser:
                if usr.lifter_id is not None:
                    banned = False
    else:
        banned = False
        dbUser = GuildMembers.query.filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == session["user_id"]).first()
        if not dbUser:
            banned = False
        else:
            banned = dbUser.banned
    return banned

def update_user_status(guild_id, username, user_key=None):
    if user_unauthenticated():
        ip_address = get_client_ipaddr()
        status = {
            'authenticated': False,
            'avatar': None,
            'manage_embed': False,
            'ip_address': ip_address,
            'username': username,
            'nickname': None,
            'user_key': user_key,
            'guild_id': guild_id,
            'user_id': session['user_id'],
            'banned': checkUserBanned(guild_id, ip_address),
            'revoked': checkUserRevoke(guild_id, user_key),
        }
        if status['banned'] or status['revoked']:
            session['user_keys'].pop(guild_id, None)
            return status
        dbUser = UnauthenticatedUsers.query.filter(and_(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key)).first()
        dbUser.bumpTimestamp()
        if dbUser.username != username or dbUser.ip_address != ip_address:
            dbUser.username = username
            dbUser.ip_address = ip_address
            db.session.commit()
    else:
        status = {
            'authenticated': True,
            'avatar': session["avatar"],
            'manage_embed': check_user_can_administrate_guild(guild_id),
            'username': username,
            'nickname': None,
            'discriminator': session['discriminator'],
            'guild_id': guild_id,
            'user_id': session['user_id'],
            'banned': checkUserBanned(guild_id),
            'revoked': checkUserRevoke(guild_id)
        }
        if status['banned'] or status['revoked']:
            return status
        dbMember = get_guild_member(guild_id, status["user_id"])
        if dbMember:
            status["nickname"] = dbMember.nickname
        dbUser = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == status['user_id'])).first()
        dbUser.bumpTimestamp()
    return status

def check_user_in_guild(guild_id):
    if user_unauthenticated():
        return guild_id in session.get("user_keys", {})
    else:
        dbUser = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == session['user_id'])).first()
        return dbUser is not None and not checkUserRevoke(guild_id)

def get_member_roles(guild_id, user_id):
    q = db.session.query(GuildMembers).filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == user_id).first()
    return json.loads(q.roles)

def get_guild_channels(guild_id, force_everyone=False):
    if user_unauthenticated() or force_everyone:
        member_roles = [guild_id] #equivilant to @everyone role
    else:
        member_roles = get_member_roles(guild_id, session['user_id'])
        if guild_id not in member_roles:
            member_roles.append(guild_id)
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    guild_channels = json.loads(dbguild.channels)
    guild_roles = json.loads(dbguild.roles)
    guild_owner = str(dbguild.owner_id)
    result_channels = []
    for channel in guild_channels:
        if channel['type'] == "text":
            result = {"channel": channel, "read": False, "write": False, "mention_everyone": False}
            if guild_owner == session.get("user_id"):
                result["read"] = True
                result["write"] = True
                result["mention_everyone"] = True
                result_channels.append(result)
                continue
            channel_perm = 0

            # @everyone
            for role in guild_roles:
                if role["id"] == guild_id:
                    channel_perm |= role["permissions"]
                    continue

            # User Guild Roles
            for m_role in member_roles:
                for g_role in guild_roles:
                    if g_role["id"] == m_role:
                        channel_perm |= g_role["permissions"]
                        continue

            # If has server administrator permission
            if user_has_permission(channel_perm, 3):
                result["read"] = True
                result["write"] = True
                result["mention_everyone"] = True
                result_channels.append(result)
                continue

            denies = 0
            allows = 0

            # channel specific
            for overwrite in channel["permission_overwrites"]:
                if overwrite["type"] == "role" and overwrite["id"] in member_roles:
                    denies |= overwrite["deny"]
                    allows |= overwrite["allow"]

            channel_perm = (channel_perm & ~denies) | allows

            # member specific
            for overwrite in channel["permission_overwrites"]:
                if overwrite["type"] == "member" and overwrite["id"] == session.get("user_id"):
                    channel_perm = (channel_perm & ~overwrite['deny']) | overwrite['allow']
                    break

            result["read"] = user_has_permission(channel_perm, 10)
            result["write"] = user_has_permission(channel_perm, 11)
            result["mention_everyone"] = user_has_permission(channel_perm, 17)

            # If default channel, you can read
            if channel["id"] == guild_id:
                result["read"] = True

            # If you cant read channel, you cant write in it
            if not user_has_permission(channel_perm, 10):
                result["read"] = False
                result["write"] = False
                result["mention_everyone"] = False

            result_channels.append(result)
    return sorted(result_channels, key=lambda k: k['channel']['position'])