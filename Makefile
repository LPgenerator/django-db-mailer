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
	@flake8 --exclude=migrations,south_migrations --ignore=F401 dbmail

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

.PHONY: run-celery
# target: run-celery - Run celery daemon
run-celery:
	@cd demo && python manage.py celeryd --loglevel=info -Q default --maxtasksperchild=10000

.PHONY: shell
# target: shell - Run project shell
shell:
	@cd demo && ./manage.py shell_plus --print-sql || ./manage.py shell

.PHONY: run-redis
# target: run-redis - Run Redis daemon
run-redis:
	@redis-server >& /dev/null &

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

kill_server:
	@ps aux|grep [r]unserver|awk '{print $2}'|xargs kill -9 >& /dev/null; true
	@ps aux|grep [r]unsslserver|awk '{print $2}'|xargs kill -9 >& /dev/null; true
