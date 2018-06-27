import pytest
import logging
from ttdex.extractor import main, validate_config, PredefinedTemplates

@pytest.fixture
def config_skeleton():
    return {
        "debug": True,
        "base_url": "https://apisb.thetradedesk.com/v3",
        "login": "login",
        "#password": "password",
        "extract_predefined": None
    }

@pytest.mark.parametrize("predefined", [
        {
            "campaign_templates": {
                "campaign_ids": ["foobar"]
            },
            "sitelists_summary": {
                "iterations": [
                    {
                        "AdvertiserId": "304zmgy",
                    }
                ]
            }
        }, # both campaign_templates and siteslits_summary
        {
            "sitelists_summary": {
                "iterations": [
                    {
                        "AdvertiserId": "304zmgy",
                    }
                ]
            }
        }, # just sitelist_summary
        {
            "campaign_templates": {
                "campaign_ids": ["foobar"]
                }
        } # just campaign_templates
])
def test_validating_config(predefined):
    assert PredefinedTemplates(predefined)

def test_validating_full_config(config_skeleton):
    config_skeleton["extract_predefined"] = {
        "campaign_templates": {
            "campaign_ids": ["foobar"]
        },
        "sitelists_summary": {
            "iterations": [
                {
                    "AdvertiserId": "304zmgy",
                }
            ]
        }
}
    assert validate_config(config_skeleton)
