from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='collective.eventmanager',
      version=version,
      description="Event manager for plone.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone event manager',
      author='Joel Kleier',
      author_email='joel.kleier@gmail.com',
      url='http://github.com/zombified/collective.eventmanager',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.CMFPlone',
          'Products.CMFPlacefulWorkflow',
          'plone.app.dexterity [grok]',
          'plone.app.referenceablebehavior',
          'plone.app.relationfield',
          'plone.namedfile [blobs]',
          'collective.z3cform.datagridfield>=0.11',
          'plone.directives.dexterity',
          'plone.directives.form',
          'Solgema.fullcalendar',
          'z3c.jbot',
          'collective.z3cform.mapwidget',
          'collective.geo.geographer',
          'collective.geo.mapwidget',
          'plone.resource',
          'plone.protect',
          'mako'
      ],
      extras_require={
            'test': ['plone.app.testing', ]
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      #setup_requires=["PasteScript"],
      #paster_plugins=["ZopeSkel"],
      )
