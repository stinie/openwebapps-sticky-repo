from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='openwebapps-stickyrepo',
      version=version,
      description="Open Web Apps repository sync",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Ian Bicking',
      author_email='ianb@mozilla.org',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'WebOb',
      ],
      entry_points="""

      """,
      )
