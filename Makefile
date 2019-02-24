FILES=*.py rocketbot tests

all: mypy lint sort_import

push: update test mypy lint verify_import
	git push

update:
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

test:
	pytest

mypy:
	mypy .

lint:
	flake8 $(FILES)

sort_import:
	isort -rc $(FILES)

verify_import:
	isort --check-only -rc $(FILES)
