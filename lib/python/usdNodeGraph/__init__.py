import logging
import os

loggingLevel = os.environ.get('USD_NODEGRAPH_DEBUG', 'WARNING').upper()
level = getattr(logging, loggingLevel)

logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

