.PHONY: clean
# target: clean - Clean temporary files
clean: clean-build clean-pyc

clear: clean
	@true

clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr *.egg-info

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +

.PHONY: clean-celery
# target: clean-celery - Clean all celery queues
clean-celery:
	@cd demo && python manage.py celery purge -f

.PHONY: pep8
# target: pep8 - Check code for pep8 rules
pep8:
	@flake8 dbmail --ignore=E402,E731,F401,F401 --exclude=migrations

.PHONY: release
# target: release - Release app into PyPi
release: clean
	@python setup.py register sdist upload --sign
	@python setup.py bdist_wheel upload --sign

.PHONY: sphinx
# target: sphinx - Make app docs
sphinx:
	@rm -rf ./docs/.build/html/
	@cd docs && sphinx-build -b html -d .build/doctrees . .build/html
	@xdg-open docs/.build/html/index.html >& /dev/null || open docs/.build/html/index.html >& /dev/null || true

sdist: clean
	@python setup.py sdist
	@ls -l dist

.PHONY: run
# target: run - Run Django development server
run: kill_server
	@cd demo && python manage.py runserver --traceback

run-server: run

.PHONY: run-uwsgi-server
# target: run-uwsgi-server - Run uWSGI server
run-uwsgi-server:
	@cd demo && uwsgi --http-socket 127.0.0.1:9000 --master --processes 8 \
	--home ~/.virtualenvs/django-db-mailer --wsgi demo.wsgi \
	--no-orphans --vacuum --http-keepalive \
	--optimize 2 --buffer-size 65536 --post-buffering 32768 \
	--cpu-affinity 1 --max-requests 10000 \
	--limit-as 1024 --listen 1024 \
	--enable-threads --threads 8 --thunder-lock --disable-logging

.PHONY: run-celery
# target: run-celery - Run celery daemon
run-celery:
	@cd demo && python manage.py celeryd -E -Q default -l INFO -c 8 --traceback -v 3

.PHONY: run-ab
# target: run-ab - Run apache bench
run-ab:
	@ab -k -t 10 -p demo/api.data.txt -c 100 -n 1000 http://127.0.0.1:9000/dbmail/api/

.PHONY: shell
# target: shell - Run project shell
shell:
	@cd demo && ./manage.py shell_plus --print-sql || ./manage.py shell

.PHONY: run-redis
# target: run-redis - Run Redis daemon
run-redis:
	@redis-server >& /dev/null &

.PHONY: test
# target: test - Run tests
test:
	@cd demo && ./manage.py test dbmail

.PHONY: tox
# target: tox - Run tests under tox
tox:
	@unset PYTHONPATH && tox

.PHONY: coverage
# target: coverage - Run tests with coverage
coverage:
	@cd demo && \
	coverage run --branch --source=dbmail ./manage.py test dbmail && \
	coverage report --omit="*/dbmail/test*,*/dbmail/migrations/*,*/dbmail/admin*"

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

kill_server:
	@ps aux|grep [r]unserver|awk '{print $2}'|xargs kill -9 >& /dev/null; true
	@ps aux|grep [r]unsslserver|awk '{print $2}'|xargs kill -9 >& /dev/null; true
