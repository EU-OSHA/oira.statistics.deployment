# OSHA OiRA Statistics Deployment

This package contains configuration and scripts for deploying the OSHA OiRA statistics. The buildout configuration sets up a number of metabase instances to serve the statistics and generates scripts to prime them with a database dump and tweak their settings afterwards.

# Setup

## Getting Started

Create a `buildout.cfg` like this:

    [buildout]
    extends =
        base.cfg
        secrets.cfg

    [metabase-instance]
    metabase-host = oira.local

Adapt `metabase-host` to the address you want to bind to or leave empty to use the default (`localhost`).

## Installation / Update

### One-Shot

If you're installing for the first time, you need to make sure the databases are created (see below). If you're updating an existing installation, it's usually enough to call

    # make all

This sets up everything in one go except for creating the databases - you may need to do this as a privileged user, and it's unnecessary to run on every update, so it's not included by default. See "Creating the Databases" for instructions.

### Step-By-Step

If the one-shot setup fails for some reason or you're interested in the details, read on for a step-by-step setup.

Decrypt the secrets with:

    # gpg -d secrets.cfg.gpg > secrets.cfg

or create your own `secrets.cfg` like this:

    [metabase-instance]
    metabase-password = ********
    ldap-password = ********

    [metabase-global]
    statistics-user = userid ******** firstname lastname

    [metabase-eu]
    statistics-user = userid ******** firstname lastname

    [metabase-fr]
    statistics-user = userid ******** firstname lastname

Then, as usual, run:

    # bin/buildout

Alternatively, decrypting and running buildout is done by

    # make buildout

### Creating the Databases

During the first setup or if you get an error like

    psql: FATAL:  database "xyz" does not exist

you will need to initialize the postgresql databases. Make sure

* buildout has run sucessfully (`make buildout` or `bin/buildout`)
* `PSQL_USER` (see Makefile) is set to a user who may create postgresql databases
* your current user can use sudo to become `PSQL_USER`

Once you're set, run

    # make create-databases

or, if you're already logged in as an appropriate user

    # psql -U postgres < scripts/create-databases.sql

and then retry `make all`.

# Usage

## Getting started

If you've run `make all` successfully, you can skip this section.

To set up the metabase instances:

    # bin/init-metabase

or

    # make init-metabase

This calls `bin/init-metabase-instance` (see below) for all instances with the parameters specified in the corresponding buildout sections.

After that you can log in to the metabase instances with the credentials you provided.

## Making changes

To make changes to the metabase content, use metabase-instance (not metabase-global or one of the country specific ones). Ideally you should have the same version of postgresql and pg_dump installed as specified at the top of the database dump file in the `dumps/` directory. It's recommended to use the master instance on our test server.

To get a clean start, restore the database from the checked-in dump:

    # bin/restore-metabase

Then make your changes through the metabase UI. To dump the database, run:

    # bin/dump-metabase

Then inspect and, if satisfied, commit the changes to the database dump in the `dumps/` directory.

To apply the changes to the global and country instances, again run

    # bin/init-metabase

## init-metabase-instance

Apply settings to a single metabase instance. Sets database connection parameters and optionally creates an additional user. Run `init-metabase-instance --help` for arguments.
