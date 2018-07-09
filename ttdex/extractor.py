from ttdapi.client import TTDClient, BaseTTDClient
import voluptuous as vp
from itertools import tee

import csv
import json
import logging
import sys
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def PredefinedTemplates(config):
    return vp.Schema({
        vp.Optional("campaign_templates"): {
            "campaign_ids": [str]
        },
        vp.Optional("sitelists_summary"): {
            "iterations": [
                vp.Schema(
                    {
                        "AdvertiserId": str
                    },
                    extra=vp.ALLOW_EXTRA)
            ]
        }
    },
                     extra=vp.ALLOW_EXTRA)(config)


def validate_config(params):
    logger.info("Validating config")
    schema = vp.Schema({
        "login": str,
        "#password": str,
        vp.Optional("debug"): bool,
        "base_url": str,
        "extract_predefined": PredefinedTemplates
    }
    )
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
        logger.info("Extrating sitelists")
        for batch in params:
            logger.info(batch)
            for chunk in self.get_all_sitelists(batch):
                # api returns {"Result": [{actual_ sitelists}, {here}], "PageStartIndex": xx}
                for sitelist in chunk['Result']:
                    yield sitelist
        logger.info("Sitelists extracted")

    def extract_campaign_templates(self, campaign_ids):
        """
        https://apisb.thetradedesk.com/v3/doc/api/post-sitelist-query-advertiser

        """
        logger.info("Extrating campaign templates")
        for campaign_id in campaign_ids:
            logger.info("downloading template for campaign_id %s", campaign_id)
            template = self.get_campaign_template(campaign_id)
            yield {
                "CampaignId": campaign_id,
                "template": template
            }
        logger.info("campaign templates extracted")

    def extract_adgroup_templates(self, campaign_ids):
        logger.info("Extracting adgroup templates for campaigns")
        for campaign_id in campaign_ids:
            payload = {
                'CampaignId': campaign_id
            }
            logger.info("downloading adgroup templates for campaign_id %s", campaign_id)
            adgroup_templates = self.post_paginated(
                'adgroup/query/campaign',
                json_payload=payload
                )
            for page in adgroup_templates:
                for template in page["Result"]:
                    yield {
                        "CampaignId": campaign_id,
                        "AdgroupId": template["AdGroupId"],
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
        logger.info("Saving to %s", outpath)
        _header, stream_of_data = tee(original_stream)
        try:
            header = next(_header).keys()
        except StopIteration:
            logger.info("empty data, didn't save anything")
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



def main(datadir, params):
    _datadir = Path(datadir)
    intables = _datadir / 'in/tables'
    outtables = _datadir / 'out/tables'

    ex = TTDExtractor(login=params['login'],
                      password=params["#password"],
                      base_url=params["base_url"])
    config_campaign_templates = params["extract_predefined"].get("campaign_templates")
    if config_campaign_templates is not None:
        with ex:
            templates = ex.extract_campaign_templates(
                config_campaign_templates["campaign_ids"])
            out = ex.serialize_response_to_json(
                templates,
                outtables / "campaign_templates.csv")

    config_adgroup_templates = params["extract_predefined"].get("adgroup_templates")
    if config_adgroup_templates is not None:
        with ex:
            templates = ex.extract_adgroup_templates(config_adgroup_templates["campaign_ids"])
            out = ex.serialize_response_to_json(templates, outtables / "adgroup_templates.csv")

    config_sitelists = params["extract_predefined"].get("sitelists_summary")
    if config_sitelists is not None:
        with ex:
            sitelists = ex.extract_sitelists(config_sitelists['iterations'])
            out = ex.serialize_response_to_json(sitelists, outtables / "sitelists_summary.csv")
