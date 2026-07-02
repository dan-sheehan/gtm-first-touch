.PHONY: install doctor start stop status seed reseed lint

install:
	python3 -m pip install -r requirements.txt

doctor:
	python3 scripts/doctor.py

start:
	./hub start

stop:
	./hub stop

status:
	./hub status

seed:
	python3 scripts/seed_demo.py seed

reseed:
	python3 scripts/seed_demo.py reseed

lint:
	python3 -m ruff check apps scripts
