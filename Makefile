PSQL_USER = postgres

.PHONY: all buildout create-databases init-metabase restart

all: init-metabase

bin/pip:
	python3 -m venv . || virtualenv -p python3 --no-site-packages --no-setuptools . || virtualenv -p python3 --no-setuptools .
	./bin/python3 -m pip install --upgrade pip

bin/buildout: bin/pip requirements.txt
	./bin/pip install -IUr requirements.txt

.installed.cfg: bin/buildout buildout.cfg base.cfg picked-versions.cfg secrets.cfg.gpg templates/*
	gpg -d ./secrets.cfg.gpg > secrets.cfg
	./bin/buildout

buildout: .installed.cfg

create-databases: .installed.cfg
	sudo -u ${PSQL_USER} psql -U postgres < ./scripts/create-databases.sql

init-metabase: .installed.cfg
	./bin/init-metabase

restart:
	./bin/supervisord || ( ./bin/supervisorctl reread && ./bin/supervisorctl restart all)
