clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

pep8:
	flake8 --exclude=migrations dbmail

release: clean
	python setup.py register sdist upload --sign
	python setup.py bdist_wheel upload --sign

sphinx:
	cd docs && sphinx-build -b html -d .build/doctrees . .build/html

sdist: clean
	python setup.py sdist
	ls -l dist

makemessages:
	cd demo && python manage.py makemessages --all --no-location --symlinks

compilemessages:
	cd demo && python manage.py compilemessages

run_server:
	cd demo && python manage.py runserver --traceback

run_celery:
	cd demo && python manage.py celeryd --loglevel=info

run_shell:
	cd demo && python manage.py shell_plus --print-sql

run_redis:
	redis-server >& /dev/null &
