# The trade desk Extractor for Keboola connection (STILL UNDER HEAVY DEV)

Can create campaigns and adgroups

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
  "extract_predefined": {
    "campaign_templates": {
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
```javascript
{
 "campaign_templates": {
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
