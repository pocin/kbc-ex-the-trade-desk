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

## Predefined endpoints
### Get campaign templates

https://apisb.thetradedesk.com/v3/doc/api/get-campaign-template-campaignid

```javascript
{
 "campaign_templates": {
    "campaign_ids": ["foobar666", "bazbaz42"]
  }
}
```

### Get adgroup templates
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
