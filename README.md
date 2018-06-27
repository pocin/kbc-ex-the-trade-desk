# The trade desk Extractor for Keboola connection (STILL UNDER HEAVY DEV)

Can create campaigns and adgroups

# Configuration
```javascript
{
  "debug": true,
  "base_url": "https://apisb.thetradedesk.com",
  "login": "foo",
  "#password": "foo",
  "extract_predefined": [
     One of predefined endpoints below
  ]
}
```

## Predefined endpoints
### Get campaign templates
```javascript
{
 "name": "campaign_templates",
 "parameters": {
  "campaign_ids": ["foobar666", "bazbaz42"']
  }
}
```

### Get sitelists summaries
https://apisb.thetradedesk.com/v3/doc/api/post-sitelist-query-advertiser

Will output a table `sitelists_summary.csv`.
```javascript
{
 "name": "sitelists_summary",
 "parameters": [
    {
      "AdvertiserId": "foobar666",
      "SearchTerms": ["term1", "term2"]
    },
    {
      "AdvertiserId": "hamspam42",
      "SearchTerms": ["shrobbery"]
    }
 ]
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
