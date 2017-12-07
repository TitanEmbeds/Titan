from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .guilds import Guilds
from .unauthenticated_users import UnauthenticatedUsers
from .unauthenticated_bans import UnauthenticatedBans
from .authenticated_users import AuthenticatedUsers
from .guild_members import GuildMembers, list_all_guild_members, get_guild_member
from .keyvalue_properties import KeyValueProperties, set_keyvalproperty, get_keyvalproperty, getexpir_keyvalproperty, setexpir_keyvalproperty, ifexists_keyvalproperty, delete_keyvalproperty
from .messages import Messages, get_channel_messages
from .cosmetics import Cosmetics, set_badges, get_badges, add_badge, remove_badge
from .user_css import UserCSS
from .administrators import Administrators, get_administrators_list
from .titan_tokens import TitanTokens, get_titan_token
from .token_transactions import TokenTransactions
from .patreon import Patreon

def set_titan_token(user_id, amt_change, action):
    token_count = get_titan_token(user_id)
    if token_count >= 0:
        token_usr = db.session.query(TitanTokens).filter(TitanTokens.user_id == user_id).first()
    else:
        token_count = 0
        token_usr = TitanTokens(user_id, 0)
    new_token_count = token_count + amt_change
    if new_token_count < 0:
        return False
    transact = TokenTransactions(user_id, action, amt_change, token_count, new_token_count)
    db.session.add(transact)
    token_usr.tokens = new_token_count
    db.session.add(token_usr)
    db.session.commit()
    return True