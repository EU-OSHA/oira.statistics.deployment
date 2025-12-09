from setuptools import find_packages
from setuptools import setup


version = "1.1.1"

setup(
    name="oira.statistics.deployment",
    version=version,
    description="Deployment helpers for the statistics of the OSHA-OiRA site.",
    long_description=open("README.md").read() + "\n" + open("CHANGES.txt").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="euphorie osha oira",
    author="syslab.com",
    author_email="info@syslab.com",
    url="http://www.oiraproject.eu/",
    license="GPL",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["oira", "oira.statistics"],
    include_package_data=True,
    python_requires="~= 3.8",
    install_requires=[
        "alembic",
        "metabase-api",
        "setuptools",
        "SQLAlchemy[postgresql] >=1.2.999999",
    ],
    entry_points="""
    [console_scripts]
    init-metabase-instance = oira.statistics.deployment.scripts:init_metabase_instance
    """,
)
