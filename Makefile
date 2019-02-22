
all: mypy lint

push: update mypy lint
	git push

update:
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

mypy:
	mypy .

lint:
	flake8 --ignore E501 main.py
	flake8 --ignore E501 rocketbot/
