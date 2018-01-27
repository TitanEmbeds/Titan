#!/usr/bin/python3
import os
import sys
if sys.platform == 'win32':
    pybabel = 'flask\\Scripts\\pybabel'
else:
    pybabel = 'pybabel'
try:
    os.unlink('titanembeds/translations/messages.pot')
except:
    pass
os.system(pybabel + ' extract -F babel.cfg -k lazy_gettext -o titanembeds/translations/messages.pot titanembeds')
os.system(pybabel + ' update -i messages.pot -d titanembeds/translations')