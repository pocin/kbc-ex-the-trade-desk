from ttdex.extractor import main, validate_config
from keboola.docker import Config
import sys
import requests
import logging
import os


if __name__ == "__main__":
    try:

        datadir = os.getenv("KBC_DATADIR", "/data/")
        cfg = Config(datadir)
        params = validate_config(cfg.get_parameters())
        if params.get('debug'):
            logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
            logging.debug("Debug mode activated")
        else:
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
            logging.debug("Logging active")
        main(datadir, params)
    except (ValueError, KeyError, requests.HTTPError) as err:
        logging.error(err)
    except:
        logging.exception("Internal error")
