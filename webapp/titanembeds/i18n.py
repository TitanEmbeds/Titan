from titanembeds.utils import babel
from flask import request

LANGUAGES = {
    'en-US': 'English'
}

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())