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
        "description": "Are your users multilingual? No worries, Titan can speak multiple languages! Check the about page for a list of all language parameters Titan can support. <br> Wish Titan supported your language? Consider contributing to <a href=\"http://translate.titanembeds.com/\" target=\"_blank\">our CrowdIn project</a>!",
        "example": "nl_NL",
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
    {
        "name": "userscalable",
        "type": "boolean",
        "description": "Enables pinch-to-zoom and auto zoom on input fields for most mobile browsers on touch-enabled devices. Disabling this will give your embed a more app-like experience. Keep in mind that disabling this might prevent accessibility features disabled people rely on from functioning.",
        "example": "false",
        "options": [
            {
                "name": "true",
                "default": True,
            },
            {
                "name": "false",
                "default": False,
            },
        ],
    },
]

LANGUAGES = [
    {
        "code": "ca_ES",
        "name_en": "Catalan",
        "name": "Català",
        "translators": [
            {
                "name": "jan",
                "crowdin_profile": "test83318",
            },
            {
                "name": "Jaime Muñoz Martín",
                "crowdin_profile": "jmmartin_5",
            },
        ],
    },{
        "code": "cs_CZ",
        "name_en": "Czech",
        "name": "čeština",
        "translators": [
            {
                "name": "Roman Hejč",
                "crowdin_profile": "romanhejc",
            },
            {
                "name": "Tom Silvestr",
                "crowdin_profile": "rescool",
            },
        ],
    },
    {
        "code": "da_DK",
        "name_en": "Danish",
        "name": "Dansk",
        "translators": [
            {
                "name": "Victor Fisker",
                "crowdin_profile": "victorfrb",
            },
        ],
    },
    {
        "code": "de_DE",
        "name_en": "German",
        "name": "Deutsch",
        "translators": [
            {
                "name": "futureyess22",
                "crowdin_profile": "futureyess22",
            },
            {
                "name": "Sascha Greuel",
                "crowdin_profile": "SoftCreatR",
            },
        ],
    },
    {
        "code": "en_US",
        "name_en": "English",
        "name": "English",
        "translators": [
            {
                "name": "Tornado1878",
                "crowdin_profile": "Tornado1878",
            },
        ],
    },
    {
        "code": "es_ES",
        "name_en": "Spanish",
        "name": "Español",
        "translators": [
            {
                "name": "jmromero",
                "crowdin_profile": "jmromero",
            },
            {
                "name": "NeHoMaR",
                "crowdin_profile": "NeHoMaR",
            },
            {
                "name": "Jaime Muñoz Martín",
                "crowdin_profile": "jmmartin_5",
            },
        ],
    },
    {
        "code": "fr_FR",
        "name_en": "French",
        "name": "français",
        "translators": [
            {
                "name": "𝔻𝕣.𝕄𝕦𝕣𝕠𝕨",
                "crowdin_profile": "drmurow",
            },
        ],
    },
    {
        "code": "hi_IN",
        "name_en": "Hindi",
        "name": "हिंदी",
        "translators": [
            {
                "name": "jznsamuel",
                "crowdin_profile": "jasonsamuel88",
            },
        ],
    },
    {
        "code": "hu_HU",
        "name_en": "Hungarian",
        "name": "Magyar",
        "translators": [
            {
                "name": "János Erkli",
                "crowdin_profile": "erklijani0521",
            },
            {
                "name": "csongorhunt",
                "crowdin_profile": "csongorhunt",
            },
        ],
    },
    {
        "code": "id_ID",
        "name_en": "Indonesian",
        "name": "bahasa Indonesia",
        "translators": [
            {
                "name": "isaideureka",
                "crowdin_profile": "isaideureka",
            },
            {
                "name": "riesky",
                "crowdin_profile": "riesky",
            },
        ],
    },
    {
        "code": "it_IT",
        "name_en": "Italian",
        "name": "Italiano",
        "translators": [
            {
                "name": "dotJS",
                "crowdin_profile": "justdotJS",
            },
        ],
    },
    {
        "code": "ja_JP",
        "name_en": "Japanese",
        "name": "日本語",
        "translators": [
            {
                "name": "Jacob Ayeni",
                "crowdin_profile": "MehItsJacob",
            },
        ],
    },
    {
        "code": "nl_NL",
        "name_en": "Dutch",
        "name": "Nederlands",
        "translators": [
            {
                "name": "jelle619",
                "crowdin_profile": "jelle619",
            },
            {
                "name": "Reeskikker",
                "crowdin_profile": "Reeskikker",
            },
            {
                "name": "SuperVK",
                "crowdin_profile": "SuperVK",
            },
        ],
    },
    {
        "code": "pl_PL",
        "name_en": "Polish",
        "name": "Polski",
        "translators": [
            {
                "name": "That Guy",
                "crowdin_profile": "maksinibob",
            },
        ],
    },
    {
        "code": "pt_BR",
        "name_en": "Portuguese",
        "name": "Português",
        "translators": [
            {
                "name": "Miguel Dos Reis",
                "crowdin_profile": "siersod",
            },
        ],
    },
    {
        "code": "ro_RO",
        "name_en": "Romanian",
        "name": "Română",
        "translators": [
            {
                "name": "Andra",
                "crowdin_profile": "sarmizegetusa",
            },
        ],
    },
    {
        "code": "sl_SI",
        "name_en": "Slovenian",
        "name": "Slovenščina",
        "translators": [
            {
                "name": "Obrazci Mail",
                "crowdin_profile": "spamamail64",
            },
        ],
    },
    {
        "code": "sr_Cyrl",
        "name_en": "Serbian (Cyrillic)",
        "name": "Српски",
        "translators": [
            {
                "name": "\"adriatic\" Miguel Dos Reis",
                "crowdin_profile": "siersod",
            },
            {
                "name": "Ciker",
                "crowdin_profile": "CikerDeveloper",
            },
        ],
    },
    {
        "code": "sr_Latn",
        "name_en": "Serbian (Latin)",
        "name": "Српски",
        "translators": [
            {
                "name": "Ciker",
                "crowdin_profile": "CikerDeveloper",
            },
        ],
    },
    {
        "code": "sv_SE",
        "name_en": "Swedish",
        "name": "svenska",
        "translators": [
            {
                "name": "Samuel Sandstrom",
                "crowdin_profile": "ssandstrom95",
            },
        ],
    },
    {
        "code": "th_TH",
        "name_en": "Thai",
        "name": "ไทย",
        "translators": [
            {
                "name": "Pantakarn Toopprateep",
                "crowdin_profile": "CardKunG",
            },
        ],
    },
    {
        "code": "tr_TR",
        "name_en": "Turkish",
        "name": "Türk",
        "translators": [
            {
                "name": "monomyth",
                "crowdin_profile": "monomyth",
            },
        ],
    },
    {
        "code": "zh_Hans_CN",
        "name_en": "Chinese Simplified",
        "name": "简体中文",
        "translators": [
            {
                "name": "dotJS",
                "crowdin_profile": "justdotJS",
            },
            {
                "name": "myjourney in Steemit",
                "crowdin_profile": "myjourney",
            },
        ],
    },
    {
        "code": "zh_Hant_TW",
        "name_en": "Chinese Traditional",
        "name": "中国传统的",
        "translators": [
            {
                "name": "myjourney in Steemit",
                "crowdin_profile": "myjourney",
            },
        ],
    },
]
