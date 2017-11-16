#!flask/bin/python
import os
import sys
if sys.platform == 'win32':
    pybabel = 'flask\\Scripts\\pybabel'
else:
    pybabel = 'pybabel'
os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o messages.pot titanembeds')
os.system(pybabel + ' update -i messages.pot -d titanembeds/translations')
os.unlink('messages.pot')