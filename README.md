# OSHA OiRA Statistics Deployment

This package contains configuration and scripts for deploying the OSHA OiRA statistics. The buildout configuration sets up a number of metabase instances to serve the statistics and generates scripts to manage them.

# Setup

## Quickstart

Create a `buildout.cfg` like this:

    [buildout]
    extends =
        base.cfg
        secrets.cfg

    [secrets]
    <= secrets-production

Run

    # make


## Installation / Update

### One-Shot

If you're installing for the first time, you need to make sure the databases are created (see below). If you're updating an existing installation, it's usually enough to call

    # make

or, equivalently,

    # make all

This sets up everything in one go except for creating the databases - you may need to do this as a privileged user, and it's unnecessary to run on every update, so it's not included by default. See "Creating the Databases" for instructions.

### Step-By-Step

If the one-shot setup fails for some reason or you're interested in the details, read on for a step-by-step setup.

If you're in an environment with managed secrets, decrypt the secrets file with:

    # gpg -d secrets.cfg.gpg > secrets.cfg

Create a `buildout.cfg` that extends `base.cfg` and, if you're using it, `secrets.cfg`.

    [buildout]
    extends =
        base.cfg
        secrets.cfg

Make sure that there is a secrets section in your `buildout.cfg` and that it inherits from the correct section in `secrets.cfg.gpg`:

    [secrets]
    <= secrets-production

Otherwise set the passwords manually:

    [secrets]
    metabase-password = secret
    ldap-password = secret

If you want to bind to a different address than `localhost`, set the `metabase-host`:

    [metabase-instance]
    metabase-host = oira.local

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

After that you can log in to the metabase instances with the credentials you provided in the buildout configuration.

## Making changes

To make changes to the metabase content, modify the data in oira.statistics.deployment.content. It may be convenient to make changes via the UI and then get the corresponding values via the API. You can use the `ipybase` shell defined in devel.cfg for this purpose.

To apply the changes to the global and country instances, again run

    # bin/init-metabase

## init-metabase-instance

Applies settings to a single metabase instance. Sets database connection parameters and optionally creates an additional user. Run `init-metabase-instance --help` for arguments.

## init-metabase

Initializes all metabase instances by dropping all database content and running
init-metabase-instance on each of them. Does not take any parameters; buildout writes
them directly into the script. If the environment variable `SKIP_DB_RESTORE` is set, database contents are not dropped but kept.
