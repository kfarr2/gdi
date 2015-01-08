.PHONY: run clean migrate test cover

run:
	./manage.py runserver 0.0.0.0:8000

clean:
	find -iname "*.pyc" -delete
	find -iname "__pychache__" -delete

migrate:
	./manage.py syncdb
	./manage.py migrate

test:
	./manage.py test

cover:
	coverage run ./manage.py test && coverage html
