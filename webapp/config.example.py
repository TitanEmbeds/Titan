config = {
    # Create an app over here https://discordapp.com/developers/applications/me
    # and fill these fields out
    'client-id': "Bot - Client ID",
    'client-secret': "Bot - Secret",
    'bot-token': "Bot - Token",

    # Rest API in https://developer.paypal.com/developer/applications
    'paypal-client-id': "Paypal client id",
    'paypal-client-secret': "Paypal client secret",

    # V2 reCAPTCHA from https://www.google.com/recaptcha/admin
    'recaptcha-site-key': "reCAPTCHA v2 Site Key",
    'recaptcha-secret-key': "reCAPTCHA v2 Secret Key",

    # Patreon
    'patreon-client-id': "Patreon client id",
    'patreon-client-secret': "Patreon client secret",

    'app-location': "/var/www/Titan/webapp/",
    'app-secret': "Type something random here, go wild.",

    'database-uri': "driver://username:password@host:port/database",
    'redis-uri': "redis://",
    'websockets-mode': "LITTERALLY None or eventlet or gevent",
    'engineio-logging': False,

    # https://titanembeds.com/api/webhook/discordbotsorg/vote
    'discordbotsorg-webhook-secret': "Secret Code - Authencation Header",
}
