PSQL_USER = postgres

.PHONY: all buildout clean create-databases init-metabase restart

all: init-metabase

bin/pip:
	python3 -m venv . || virtualenv -p python3 --no-site-packages --no-setuptools . || virtualenv -p python3 --no-setuptools .
	./bin/python3 -m pip install --upgrade pip

bin/buildout: bin/pip requirements.txt
	./bin/pip install -IUr requirements.txt

secrets.cfg: secrets.cfg.gpg
	gpg -d ./secrets.cfg.gpg > secrets.cfg
	chmod 600 secrets.cfg

.installed.cfg: bin/buildout buildout.cfg base.cfg picked-versions.cfg secrets.cfg templates/*
	./bin/buildout

buildout: .installed.cfg

create-databases: .installed.cfg
	sudo -u ${PSQL_USER} psql -U postgres < ./scripts/create-databases.sql

init-metabase: .installed.cfg
	./bin/init-metabase

clean: .installed.cfg
	./bin/clear-metabase

restart:
	./bin/supervisord || ( ./bin/supervisorctl reread && ./bin/supervisorctl restart all)

wait:
	./bin/wait-metabase
