.PHONY: source install run clean migrate test cover

source:
	@if not [ -d ".env" ]; then \
		virtualenv --no-site-packages -p python3 .env;
	fi
	source .env/bin/activate

install:
	@$(MAKE) source
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
