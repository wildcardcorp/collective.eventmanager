Introduction
============

An event manager for plone.

This package depends on plone.app.dexterity so make sure to pin dexterity
versions in your buildout::

    extends =
        ...
        http://good-py.appspot.com/release/dexterity/1.2.1
        ...

This package also depends on Solgema.fullcalendar, specifically at least the version at this revision: https://github.com/collective/Solgema.fullcalendar/tree/5e8724dd507aa5930a6676dd473c1752263b58cf

If you'd like to display EM Event type objects on a calendar, this package configures the EM Event type to be compatible with the Solgema.fullcalendar product. Just create a Collection (ATTopic), add criteria for the EM Event type, and switch the display for the collection to Solgema.fullcalendar.


Running the buildout
--------------------

git clone git@github.com:zombified/collective.eventmanager.git
cd collective.eventmanager
/path/to/python bootstrap.py
./bin/buildout