# The trade desk Extractor for Keboola connection (STILL UNDER HEAVY DEV)
# Configuration
```javascript
{ "debug": true,
  "base_url": "https://apisb.thetradedesk.com/v3",
  "login": "foo",
  "#password": "foo",
  "extract_predefined": {
     any of predefined endpoints below
  }
 }
```

`"base_url": "https://apisb.thetradedesk.com/v3"` for sandbox

A final config might look like this

```javascript
{ "debug": true,
  "base_url": "https://apisb.thetradedesk.com/v3",
  "login": "foo",
  "#password": "foo",
  "custom_post_paginated_queries": [
    {
      "endpoint": "sitelists/query/advertiser",
      "payload": {"AdvertiserId": "fooxuz"},
      "filename": "advertiser_fooxuz.csv"
    }
],
  "extract_predefined": {
    "campaign_templates": {
        "campaign_ids": ["foobar666", "bazbaz42"]
      },
    "adgroup_templates": {
        "campaign_ids": ["foobar666", "bazbaz42"]
      },
    "sitelists_summary": {
        "iterations": [
          {
            "AdvertiserId": "foobar666",
          },
          {
            "AdvertiserId": "hamspam42",
            "SearchTerms": ["shrobbery"] # + any parameters as described in the API
          }
      ]
    }
  }
 }
```

## Predefined requests
### Get campaign templates

https://apisb.thetradedesk.com/v3/doc/api/get-campaign-template-campaignid

```javascript
{
 "campaign_templates": {
    "campaign_ids": ["foobar666", "bazbaz42"]
  }
}
```

### Get adgroup templates (pseudo)

the campaign templates are implemented as dummy-campaigns
https://apisb.thetradedesk.com/v3/doc/api/post-adgroup-query-campaign
```javascript
{
 "adgroup_templates": {
    "campaign_ids": ["foobar666", "bazbaz42"]
  }
}
```

### Get sitelists summaries
https://apisb.thetradedesk.com/v3/doc/api/post-sitelist-query-advertiser

Will output a table `sitelists_summary.csv`.
```javascript
{
 "sitelists_summary": {
    "iterations": [
      {
        "AdvertiserId": "foobar666",
      },
      {
        "AdvertiserId": "hamspam42",
        "SearchTerms": ["shrobbery"] # + any parameters as described in the API
      }
  ]
 }
}
```

### All advertisers for partner_id

https://apisb.thetradedesk.com/v3/doc/api/post-advertiser-query-partner

`all_advertisers.csv`

```javascript
"all_advertisers": {"partner_id": "your_partner_id"}
```

### Get all campaigns for all advertisers for given partner_id
gets advetisers from https://apisb.thetradedesk.com/v3/doc/api/post-advertiser-query-partner and consequently this https://api.thetradedesk.com/v3/doc/api/post-campaign-query-advertiser endpoint to get all campaigns


Will output a table `all_campaigns_all_advertisers.csv`.
```javascript
{
 "all_campaigns_all_advertisers": {
        "partner_id": "foobar666",
        "search_terms": ["optional", "array", "of", "search terms"],
        "availabilities": ["Available"] # default
      }
}
```


### Get all adgroups for all advertisers for given partner_id
gets advetisers from https://apisb.thetradedesk.com/v3/doc/api/post-advertiser-query-partner and consequently this https://api.thetradedesk.com/v3/doc/api/post-adgroup-query-advertiser endpoint to get all adgroups


Will output a table `all_adgroups_all_advertisers.csv`.
```javascript
{
 "all_adgroups_all_advertisers": {
      {
        "partner_id": "foobar666",
        "search_terms": ["optional", "array", "of", "search terms"],
        "availabilities": ["Available"] # default
      }
}
```

### Incremental (=delta) campaigns for all advertisers for given partner_id
https://api.thetradedesk.com/v3/doc/api/post-delta-campaign-query-advertiser
the `LastChangeTrackingVersion` is cached under the hood in `state.json`

use `"reset": True` to wipe statefile and redownload everything
```javascript
{
 "delta_campaigns": {
        "partner_id": "foobar666",
        "advertisers": ["list", "of", "advetisers"], #either this or partner_id, NOT both!
        "reset": False
      }
}
```

### Incremental (=delta) adgroups for all advertisers for given partner_id
https://api.thetradedesk.com/v3/doc/api/post-delta-adgroup-query-advertiser
the `LastChangeTrackingVersion` is cached under the hood in `state.json`

use `"reset": True` to wipe statefile and redownload everything
```javascript
{
 "delta_adgroups": {
        "partner_id": "foobar666",
        "advertisers": ["list", "of", "advetisers"], #either this or partner_id, NOT both!
        "reset": False
      }
}
```

## custom queries using POST requests & paginated endpoints
such as https://api.thetradedesk.com/v3/doc/api/post-campaign-query-advertiser

make a post request to `"endpoint"` with `"payload"` as a json payload, save the output to `"filename"`. The pagination is handled implicitly.

```javascript

"custom_post_paginated_queries": [{
   "endpoint": "enpdoint/at/somehwere",
   "payload": {"literal": "json_payload", "what": ["as", expected", "by", "api"]},
   "filename": "query_name.csv"
}]


```

# Development
## Run locally
```
$ docker-compose run --rm dev
# gets you an interactive shell
# mounts the ./data/ folder to /data/
```

## Run tests
```
make test
# after dev session is finished to clean up containers..
make clean 
```
