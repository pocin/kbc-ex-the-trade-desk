from ttdapi.client import TTDClient, BaseTTDClient
from keboola.docker import Config
import voluptuous as vp
from itertools import tee

import csv
import json
import logging
import sys
from pathlib import Path
import os

def main():
    logging.info("Hello, world!")


def validate_config(params):
    schema = vp.Schema({
        "login": str,
        "#password": str,
        vp.Optional("debug"): bool,
        "evironment": vp.Any("sandbox", "production"),
        "extract": {
            vp.Optional("sitelist_summaries"): {
                "AdvertiserId": "id_here",
                vp.Optional("SearchTerms"): list,
                vp.Optional("SortFields"): list
            }
        }
    })
    return schema(params)


class TTDExtractor(TTDClient):
    def extract_sitelists(self, params):
        """
        https://apisb.thetradedesk.com/v3/doc/api/post-sitelist-query-advertiser
        Args:
            params: a list of dicts containing the json data for requests
                for example [
                                {
                                    "AdvertiserId": "foobar666",
                                    "SearchTerms": ["term1", "term2"]
                                }
                            ]



        Returns:
            dicts like this one at a time
            {"SiteListLineCount": 1, "AdvertiserId": "sample string 1",
            "SiteListId": "sample string 1", "SiteListName": "sample string 1",
            "Description": "sample string 1", "Permissions": "Global"}

        """
        for batch in params:
            for chunk in self.get_all_sitelists(batch):
                # api returns {"Result": [{actual_ sitelists}, {here}], "PageStartIndex": xx}
                for sitelist in chunk['Result']:
                    yield sitelist

    #or this?
    def extract_campaign_templates(self, campaign_ids):
        """
        https://apisb.thetradedesk.com/v3/doc/api/post-sitelist-query-advertiser

        """
        for campaign_id in campaign_ids:
            template = self.get_campaign_template(campaign_id)
            yield {
                "CampaignId": campaign_id,
                "template": template
            }

    @staticmethod
    def serialize_response_to_json(original_stream, outpath):
        """Save the stream of json objects (dicts) into csv

        Scalars are saved as columns, dicts/lists are dumped as strings

        Retruns:
            None if the stream is empty, else path to the output csv
        """
        # do not use original_stream here at all!
        _header, stream_of_data = tee(original_stream)
        try:
            header = next(_header).keys()
        except StopIteration:
            return None

        with open(outpath, 'w') as outf:
            writer = csv.DictWriter(outf, fieldnames=header)
            writer.writeheader()
            for row in stream_of_data:
                # take write scalar values as columns, but safely serialize dicts/lists into json strings
                # In case of templates the jsons are useful as they are
                # in other cases the json objects can be converted to csv in a separate component eg.
                # https://components.keboola.com/~/components/apac.processor-flatten-json
                writer.writerow(
                    {
                        key: (json.dumps(value) if isinstance(value, (dict, list)) else value)
                        for key, value
                        in row.items()
                     }
                    )
        return outpath



def _main(datadir):
    cfg = Config(datadir)
    params = validate_config(cfg.get_parameters())
    _datadir = Path(datadir)
    intables = _datadir / 'in/tables'
    if params.get('debug'):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

