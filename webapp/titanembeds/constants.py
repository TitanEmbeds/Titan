QUERY_PARAMETERS = [
    {
        "name": "css",
        "type": "integer",
        "description": "Styles the embed's theme according to the unique custom CSS ID. Custom CSS may be managed from the user dashboard page.",
        "example": "1",
    },
    {
        "name": "defaultchannel",
        "type": "snowflake",
        "description": "Instead of having the top channel as the first channel your users see, you may change it. Enable Discord's Developer mode in the Appearances tab of the User Settings and copy the channel ID.",
        "example": "1234567890",
    },
    {
        "name": "lang",
        "type": "language",
        "description": "Is your users multilingual? No worries, Titan can speak multiple languages! <a href=\"https://github.com/TitanEmbeds/Titan/blob/master/webapp/titanembeds/i18n.py\" target=\"_blank\">Check here</a> for a list of all language parameters Titan can support. <br> Wish Titan supported your language? Consider contributing to <a href=\"http://translate.titanembeds.com/\" target=\"_blank\">our CrowdIn project</a>!",
        "example": "nl",
        "input": "text",
    },
    {
        "name": "noscroll",
        "type": "boolean",
        "description": "Prevents the embed from scrolling down on first load. Useful for those who wants to set #info -typed channels as their default channel. Gotta have those good reads!",
        "example": "true",
        "options": [
            {
                "name": "true",
                "default": False,
            },
            {
                "name": "false",
                "default": True,
            },
        ],
    },
    {
        "name": "sametarget",
        "type": "boolean",
        "description": "For those who don't want the Discord Login to open in a new tab/window... (<em>Does not work for iframe loaded embeds!!!</em> This is a direct link option only.)",
        "example": "true",
        "options": [
            {
                "name": "true",
                "default": False,
            },
            {
                "name": "false",
                "default": True,
            },
        ],
    },
    {
        "name": "theme",
        "type": "string",
        "description": "Want your embed to use one of our premade themes? Look no further!",
        "example": "DiscordDark",
        "options": [
            {
                "name": "BetterTitan",
                "default": False,
            },
            {
                "name": "DiscordDark",
                "default": False,
            },
        ],
    },
    {
        "name": "username",
        "type": "string",
        "description": "Prefills the guest username field with the given username.",
        "example": "Rainbow%20Dash",
    },
]