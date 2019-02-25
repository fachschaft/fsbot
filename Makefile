FILES=*.py rocketbot tests

all: mypy lint sort_import

push: update utest mypy lint verify_import itest
	git push

update:
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

test: utest itest

utest:
	pytest tests/unit

itest:
	pytest tests/integration

test_cov:
	pytest tests --cov=./
	codecov

mypy:
	mypy .

lint:
	flake8 $(FILES)

sort_import:
	isort -rc $(FILES)

verify_import:
	isort --check-only -rc $(FILES)
