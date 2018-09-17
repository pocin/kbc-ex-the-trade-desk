# test with -k flag
testk:
	docker-compose run --rm dev python3 -m pytest -k $(what)

test:
	docker-compose run --rm dev python3 -m pytest

clean:
	docker-compose down

sh:
	docker-compose run --rm dev /bin/sh

build:
	docker-compose build dev
