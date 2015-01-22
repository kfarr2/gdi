.PHONY: install run clean migrate test cover

install:
	@if not [ -d ".env" ]; then \
		python3 -m venv .env;\
		curl https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py | python3;\
	fi
	export CPATH=/usr/include/openldap24
	export LIBRARY_PATH=/usr/lib/openldap24/
	pip install -r requirements.txt

run:
	./manage.py runserver 0.0.0.0:8000

clean:
	find -iname "*.pyc" -delete
	find -iname "__pycache__" -delete

migrate:
	./manage.py syncdb
	./manage.py migrate

test:
	./manage.py test

cover:
	coverage run ./manage.py test && coverage html
