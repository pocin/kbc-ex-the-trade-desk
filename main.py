from ttdex.extractor import main
import sys
import requests
import logging

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        main()
    except (ValueError, KeyError, requests.HTTPError) as err:
        logging.error(err)
    except:
        logging.exception("Internal error")
