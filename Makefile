FILES=*.py fsbot tests

all: mypy lint sort_import

run:
	python main.py

push: update utest mypy lint verify_import itest _check_modified
	git push

update:
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

test: utest itest

utest: _pre_test
	pytest tests/unit

itest: _pre_test
	pytest tests/integration

test_cov: _pre_test
	pytest tests --cov=fsbot
	codecov

mypy:
	mypy .

lint:
	flake8 $(FILES)

sort_import:
	isort -rc $(FILES)

verify_import:
	isort --check-only -rc $(FILES)

restart_testserver:
	sudo venv/bin/docker-compose -f docker-compose-testserver.yml down && sudo venv/bin/docker-compose -f docker-compose-testserver.yml up -d && until curl http://localhost:3000/api/v1/info; do sleep 5; echo "waiting for Rocket.Chat server to start"; done

_pre_test:
	touch bot_config.py

_check_modified:
	git diff-index --quiet HEAD