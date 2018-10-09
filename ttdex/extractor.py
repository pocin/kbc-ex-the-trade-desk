"""TTD extractor"""
import csv
import json
import logging
from itertools import tee
import time
import requests
from pathlib import Path

from typing import Iterable, Tuple, Optional, Callable

import voluptuous as vp
from ttdapi.client import TTDClient
from ttdapi.exceptions import TTDApiError

logger = logging.getLogger(__name__)


def PredefinedTemplates(config):
    return vp.Schema({
        vp.Optional("campaign_templates"): {
            "campaign_ids": [vp.Coerce(str)]
        },
        vp.Optional("adgroup_templates"): {
            "campaign_ids": [vp.Coerce(str)]
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
    schema = vp.Schema(
        {
            "login": str,
            "#password": str,
            vp.Optional("debug"): bool,
            "base_url": str,
            "extract_predefined": PredefinedTemplates
        }
    )
    return schema(params)

def load_tracking_versions(path_to_statefile, endpoint):
    with open(path_to_statefile) as f:
        state = json.load(f)
        return state.get(endpoint, dict())


class StateFile(dict):
    def save_to_file(self, path='out/state.json'):
        logger.info("Saving statefile to %s", path)
        with open(path, 'w') as outf:
            json.dump(self, outf)

class TTDExtractor(TTDClient):
    def _request(self, *args, **kwargs):
        try:
            return super()._request(*args, **kwargs)
        except (requests.HTTPError, TTDApiError)  as err:
            if err.response.status_code == 429:
                logger.info("Too many requests, waiting 65 seconds")
                time.sleep(65)
                logger.info("Retrying")
                return super()._request(*args, **kwargs)
            else:
                raise err

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
            template = self.get("/campaign/" + campaign_id)
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


    def _delta_things(
            self,
            fetch_all_delta_THING_for_advertiser: Callable,
            last_change_tracking_versions: dict,
            partner_id: str=None,
            advertisers: Optional[Iterable[str]]=None):

        if ((partner_id is None and advertisers is None) or
            (partner_id is not None and advertisers is not None)):
            raise ValueError("supply exactly one of `partner_id` or a list of `advertisers`")

        if advertisers is None:
            advertisers = [
                a['AdvertiserId']
                for a
                in self.get_all_advertisers(
                    {
                        "PartnerId": partner_id,
                        "availabilities": ["Available"]
                    })
            ]
        for advertiser_id in advertisers:
            logger.debug("Processing advertiser_id %s", advertiser_id)
            last_change_tracking_version = last_change_tracking_versions.get(advertiser_id)
            for data, tracking_version in fetch_all_delta_THING_for_advertiser(
                    advertiser_id,
                    last_change_tracking_version):
                # {id: version} is a duplication, but the overhead shouldn't
                # be too dramatic as the data is written to file right away
                yield data, {advertiser_id: tracking_version}

    def delta_campaigns(
            self,
            last_change_tracking_versions: dict,
            partner_id:str =None,
            advertisers: Optional[Iterable[str]]=None
    ) -> Iterable[Tuple[dict, dict]]:
        """The first dict in the tuple is the JSON data, the second is
        a {advertiserId: last_change_tracking_version}
        """

        yield from self._delta_things(
            self.fetch_all_delta_campaigns_for_advertiser,
            last_change_tracking_versions=last_change_tracking_versions,
            partner_id=partner_id,
            advertisers=advertisers)

    def delta_adgroups(
            self,
            last_change_tracking_versions: dict,
            partner_id:str =None,
            advertisers: Optional[Iterable[str]]=None,
            ):


        yield from self._delta_things(
            self.fetch_all_delta_adgroups_for_advertiser,
            last_change_tracking_versions=last_change_tracking_versions,
            partner_id=partner_id,
            advertisers=advertisers)

    def get_all_campaigns_all_advertisers(
            self,
            partner_id,
            search_terms=None,
            availabilities=["Available"]):
        yield from self._get_all_things_all_advertisers(
            thing='campaign',
            partner_id=partner_id,
            search_terms=search_terms,
            availabilities=availabilities)

    def get_all_adgroups_all_advertisers(
            self,
            partner_id,
            search_terms=None,
            availabilities=["Available"]):
        yield from self._get_all_things_all_advertisers(
            thing='adgroup',
            partner_id=partner_id,
            search_terms=search_terms,
            availabilities=availabilities)

    def _get_all_things_all_advertisers(
            self,
            thing,
            partner_id,
            search_terms=None,
            availabilities=['Available']):

        available_things = ("campaign", "adgroup")
        if thing not in available_things:
            raise ValueError(
                "thing must be one of {}, not {}".format(available_things,
                                                         thing))
        logger.info(
            "Fetching all %s for %s, (SearchTerms=%s), advertisers of partner_id %s",
            thing,
            search_terms,
            availabilities,
            partner_id)

        advertisers_payload = {
            "PartnerId": partner_id,
            "availabilities": availabilities
        }
        if search_terms is not None:
            advertisers_payload['SearchTerms'] = search_terms

        for advertiser in self.get_all_advertisers(advertisers_payload):
            logger.info("Processing advertiser '%s'", advertiser)
            thing_payload = {
                "AdvertiserId": advertiser['AdvertiserId']
            }
            yield from self.post_paginated(
                endpoint='{}/query/advertiser'.format(thing),
                json_payload=thing_payload,
                stream_items=True)


    @staticmethod
    def serialize_delta_stream_to_csv(original_delta_stream: Iterable[Tuple[dict, dict]],
                                      outpath):
        """A delta stream is a stream of tuples, (json_data, {advertiser_id: last_change_Tracking_version})

        We need to write the json_data to csv and cache the last_change_tracking_version
        """
        # For now a dumb copy paste of serialize_response_to_json - no time to refactor
        # will I regret?

        logger.info("Saving to %s", outpath)

        _header, delta_stream_of_data = tee(original_delta_stream, 2)

        logger.debug("Looking for header")
        for datapoint, _ in _header:
            if datapoint is not None:
                logger.debug("Found header")
                header = datapoint.keys()
                break
        else:
            # a corner case when neither of the advertisers had any data,
            # and the delta_stream is full of just tracking_versions
            tracking_versions = {}
            for _, track_version in delta_stream_of_data:
                tracking_versions.update(track_version)
            logging.info("delta_stream did not contain any data, "
                            "but was full of tracking_versions. "
                            "No tables will be in out/tables"
                            "but statefile will be updated")
            return None, tracking_versions

        tracking_versions = {}
        total_rows = 0
        written_rows = 0

        with open(outpath, 'w') as outf:
            writer = csv.DictWriter(outf, fieldnames=header)
            writer.writeheader()
            for row, last_tracking_version in delta_stream_of_data:
                # take write scalar values as columns, but safely serialize
                # dicts/lists into json strings
                # In case of templates the jsons are useful as they are
                # in other cases the json objects can be converted to csv in a
                # separate component eg.
                # https://components.keboola.com/~/components/apac.processor-flatten-json

                # if row is None it means that the delta endpoint returned
                # empty data but a new tracking version which we need to cache
                total_rows += 1
                if row is not None:

                    written_rows += 1

                    writer.writerow(
                        {
                            key: (json.dumps(value) if isinstance(value, (dict, list)) else value)
                            for key, value
                            in row.items()
                        }
                    )
                tracking_versions.update(last_tracking_version)

        print("total_rows: {}; written_rows: {}".format(total_rows, written_rows))
        return outpath, tracking_versions


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
                # take write scalar values as columns, but safely serialize
                # dicts/lists into json strings
                # In case of templates the jsons are useful as they are
                # in other cases the json objects can be converted to csv in a
                # separate component eg.
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

    state = StateFile()
    ex = TTDExtractor(login=params['login'],
                      password=params["#password"],
                      base_url=params["base_url"])

    p_predef = params.get("extract_predefined", {})
    config_campaign_templates = p_predef.get("campaign_templates")
    if config_campaign_templates is not None:
        with ex:
            campaign_templates = ex.extract_campaign_templates(
                config_campaign_templates["campaign_ids"])
            ex.serialize_response_to_json(
                campaign_templates,
                outtables / "campaign_templates.csv")

    config_adgroup_templates = p_predef.get("adgroup_templates")
    if config_adgroup_templates is not None:
        with ex:
            adgroup_templates = ex.extract_adgroup_templates(config_adgroup_templates["campaign_ids"])
            ex.serialize_response_to_json(
                adgroup_templates,
                outtables / "adgroup_templates.csv")

    config_sitelists = p_predef.get("sitelists_summary")
    if config_sitelists is not None:
        with ex:
            sitelists = ex.extract_sitelists(config_sitelists['iterations'])
            ex.serialize_response_to_json(sitelists, outtables / "sitelists_summary.csv")

    config_get_advertisers = p_predef.get("all_advertisers")
    if config_get_advertisers is not None:
        with ex:
            advertisers = ex.get_all_advertisers({"PartnerId": config_get_advertisers['partner_id']})
            ex.serialize_response_to_json(advertisers, outtables / "advertisers.csv")

    cfg_gacaa = p_predef.get("all_campaigns_all_advertisers")
    if cfg_gacaa is not None:
        with ex:
            campaigns = ex.get_all_campaigns_all_advertisers(**cfg_gacaa)
            ex.serialize_response_to_json(
                campaigns,
                outtables / "all_campaigns_all_advertisers.csv")


    cfg_gaaaa = p_predef.get("all_adgroups_all_advertisers")
    if cfg_gaaaa is not None:
        with ex:
            adgroups = ex.get_all_adgroups_all_advertisers(**cfg_gaaaa)
            ex.serialize_response_to_json(
                adgroups,
                outtables / "all_adgroups_all_advertisers.csv")

    for custom_query in params.get("custom_post_paginated_queries", []):
        with ex:
            stream = ex.post_paginated(
                endpoint=custom_query['endpoint'],
                json_payload=custom_query['payload'],
                stream_items=True)
            ex.serialize_response_to_json(
                stream,
                outtables / Path(custom_query['filename']).stem + '.csv'
            )

    cfg_delta_campaigns = p_predef.get("delta_campaigns")
    if cfg_delta_campaigns is not None:
        with ex:
            # download all advertisers
            # Iterate over them
            # If advertiser is in statefile use that last_change_tracking_version
            # serialize everything to csv
            if cfg_delta_campaigns.get('reset'):
                state_campaign_tracking_ids = {}
            else:
                state_campaign_tracking_ids = load_tracking_versions(
                    _datadir / "in/state.json",
                    "delta_campaigns")

            camp_delta_stream = ex.delta_campaigns(
                last_change_tracking_versions=state_campaign_tracking_ids,
                partner_id=cfg_delta_campaigns.get('partner_id'),
                advertisers=cfg_delta_campaigns.get('advertisers'))
            _, campaign_tracking_versions = ex.serialize_delta_stream_to_csv(
                camp_delta_stream,
                outtables / 'delta_campaigns.csv'
            )
            state["delta_campaigns"] = campaign_tracking_versions



    cfg_delta_adgroups = p_predef.get("delta_adgroups")
    if cfg_delta_adgroups is not None:
        with ex:
            # download all advertisers
            # Iterate over them
            # If advertiser is in statefile use that last_change_tracking_version
            # serialize everything to csv

            if cfg_delta_adgroups.get('reset'):
                state_adgroup_tracking_ids = {}
            else:
                state_adgroup_tracking_ids = load_tracking_versions(
                    _datadir / "in/state.json",
                    "delta_adgroups")

            adgrp_delta_stream = ex.delta_adgroups(
                last_change_tracking_versions=state_adgroup_tracking_ids,
                partner_id=cfg_delta_adgroups.get('partner_id'),
                advertisers=cfg_delta_adgroups.get('advertisers'))

            _, adgroup_tracking_versions = ex.serialize_delta_stream_to_csv(
                adgrp_delta_stream,
                outtables / 'delta_adgroups.csv'
            )

            state["delta_adgroups"] = adgroup_tracking_versions

    state.save_to_file(path= _datadir / 'out/state.json')
