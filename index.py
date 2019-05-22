#!/usr/bin/python3

import sys
from addon_scraper import create_addon_repo

print ('Number of arguments:', len(sys.argv) - 1, 'arguments.')
print ('Argument List:', str(sys.argv[1:]))

for addon in sys.argv[1:]:
    create_addon_repo(addon, True)
