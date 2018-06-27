from ttdex.extractor import TTDExtractor
import os
import json
import pytest
import csv



@pytest.fixture(scope='module')
def extractor():
    return TTDExtractor(login=os.environ["TTD_USERNAME"],
                      password=os.environ["TTD_PASSWORD"],
                      base_url='https://apisb.thetradedesk.com/v3/')


def test_serializing_responses_to_csv(tmpdir):
    ORIGINAL_ROWS = [{"scalar": 1,
                      "is_dict": {"foo": 42, "complicated":["38", True]},
                      "is_list": ["contain", {"anything": "really"}]},
                     {"scalar": 2,
                      "is_dict": {"foo": 42, "complicated":["38", True]},
                      "is_list": ["contain", {"anything": "really"}]}]
    def stream_of_responses():
        """Simulates a response from api

        The API client ensures that responses are streamed like this
        """
        for row in ORIGINAL_ROWS:
            yield row

    outpath = tmpdir.join("output.csv")

    returned_outpath = TTDExtractor.serialize_response_to_json(stream_of_responses(), outpath.strpath)

    # make sure de/serialization works ok
    with open(returned_outpath) as fin:
        reader = csv.DictReader(fin)
        for i, row in enumerate(reader):
            assert json.loads(row["is_dict"]) == ORIGINAL_ROWS[i]['is_dict']
            assert json.loads(row["is_list"]) == ORIGINAL_ROWS[i]['is_list']
            assert json.loads(row['scalar']) == ORIGINAL_ROWS[i]['scalar']


def test_extracting_sitelists(extractor):

    sitelists = list(extractor.extract_sitelists([{"AdvertiserId": "8iktwp1"}]))
    assert len(sitelists) == 0


@pytest.mark.skip(reason="there are no templates in the sandbox")
def test_extracting_campaign_templates(extractor):
    ids = ['8frjjlc']
    templates = list(extractor.extract_campaign_templates(ids))
    assert len(templates) == 1
    assert templates[0]["CampaignId"] == ids[0]
    assert templates[0]["template"] is None



