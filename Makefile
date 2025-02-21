PSQL_USER = postgres

.PHONY: all buildout clean create-databases init-metabase restart upgrade wait

all: init-metabase

.venv/bin/pip:
	python3 -m venv .venv || virtualenv -p python3 --no-site-packages --no-setuptools .venv || virtualenv -p python3 --no-setuptools .venv
	.venv/bin/python3 -m pip install --upgrade pip

.venv/bin/buildout: .venv/bin/pip requirements.txt
	.venv/bin/pip uninstall -y setuptools
	.venv/bin/pip install -IUr requirements.txt

secrets.cfg: secrets.cfg.gpg
	gpg -d ./secrets.cfg.gpg > secrets.cfg
	chmod 600 secrets.cfg

.installed.cfg: .venv/bin/buildout buildout.cfg base.cfg picked-versions.cfg secrets.cfg templates/*
	.venv/bin/buildout

buildout: .installed.cfg

create-databases: .installed.cfg
	sudo -u ${PSQL_USER} psql -U postgres < ./scripts/create-databases.sql

init-metabase: .installed.cfg
	./bin/init-metabase

clean: .installed.cfg
	./bin/clear-metabase

restart:
	./bin/supervisord || ( ./bin/supervisorctl reload)

upgrade:
	./bin/alembic -c ./etc/alembic.ini upgrade head

wait:
	./bin/wait-metabase
