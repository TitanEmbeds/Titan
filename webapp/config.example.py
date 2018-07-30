config = {
    # Create an app over here https://discordapp.com/developers/applications/me
    # and fill these fields out
    'client-id': "Your app client id",
    'client-secret': "Your discord client secret",
    'bot-token': "Discord bot token",
    
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
    'discordbotsorg-webhook-secret': "Secret code used in the authorization header for DBL webhook",
    
    # Sentry.io is used to track and upload errors
    "sentry-dsn": "Copy the dns string when creating a project on sentry",
    "sentry-js-dsn": "Same as above, but you can create a seperate sentry project to track the client side js errors",
}
