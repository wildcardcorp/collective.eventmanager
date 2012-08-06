Introduction
============

An event manager for plone.

Specifically, an event manager that groups information about events
into a folderish container -- information including registration details,
accommodation information, and session management.

This package depends on plone.app.dexterity so make sure to pin dexterity
versions in your buildout::

    extends =
        ...
        http://good-py.appspot.com/release/dexterity/1.2.1
        ...

This package also depends on Solgema.fullcalendar, specifically at least the
version at this revision: 
  
  https://github.com/collective/Solgema.fullcalendar/tree/5e8724dd507aa5930a6676dd473c1752263b58cf

If you'd like to display EM Event type objects on a calendar, this package
configures the EM Event type to be compatible with the Solgema.fullcalendar
product. Just create a Collection (ATTopic), add criteria for the EM Event
type, and switch the display for the collection to Solgema.fullcalendar.


Running the buildout
====================

git clone git@github.com:zombified/collective.eventmanager.git
cd collective.eventmanager
/path/to/python bootstrap.py
./bin/buildout

- to run buildout on mac, you need to install swig

sudo port install swig
sudo port install swig-python

- ubuntu

sudo apt-get install swig


Basic Operations
================

Structure
---------
The default folderish structure of an EM Event object is:

  EM Event
   |- Sessions (Folderish, holds 'Session' type objects)
   |- Session Calendar (Solgema.fullcalendar page that displays all Sessions on
      calendar)
   |- Registrations (Folderish, holds 'Registration' type objects)
   |- Travel Accommodations (Folderish, holds 'Accommodation' type objects)
   |- Lodging Acommodations (Folderish, holds 'Accommodation' type objects)
   |- Announcements (Folderish, holds News Item types that get displayed on the
      EM Event page)

There is also a public URL that can be used for registration:

  http://<your.site>/path/to/event/registration-form

This will present a registration form that can be completed by Anonymous users.


Registration Logic
------------------
The primary workflow for registration looks something like this:

  1. User enters registration on public registration form, registration moves
     into 'Waiting' (aka 'submitted') state.
  2. If the event requires registration approval (Max Registration is set to 0
     and waiting list is enabled on EM Event), then a manager must use the
     Registration Status page (View the event, Event Manager -> Registration
     Status) to approve, deny, cancel, or confirm a registration.
  3. If the event does not require manager approval, then a registration is
     automatically placed in an 'approved' state, waiting cancellation, denial,
     or confirmation from the user or a manager.
  4. Once a registration has been confirmed, they will show up on the event's
     Roster (view the event, Event Manager -> Roster)

During this process, the Event Manager product can be configured to send out
emails for the following events:
  - After registration (a 'thank you' message)
  - When a registration get's placed on the waiting list
  - When the event is not accepting any more registrations (registration is full)

A manager can also send out emails at any point during the registraiton process
by viewing the event, then selecting the Event Manager -> Email Sender form from
the page menu. This form allows you to send confirmation, announcement, and
other emails to registered email addresses -- all are allowed attachments.


Configuration
-------------
Most configuration for EM Event objects takes place when you create or edit an
EMEvent object. However, an administrator can modify site-wide templates from
the Site Setup page by clicking on one of several links.

Certificate PDF Templates

  This Add-on Configuration will let you modify the default text for generated
  Certificates. Each text input can be overridden when certificates are
  generated, unless they are generated automatically from the Email Sender
  form.

EM EMail Templates

  This Add-on Configuration will let you modify the default subject and body
  (text and HTML versions) values for each template.

  The template language used is Mako, and there are a few variables provided,
  depending on the email:
    - ${event_content} -- this is a string value that contains the value being
      placed into the field
    - ${emevent} -- this is the EM Event object that the email is referencing
    - ${registrations} -- this a list of all the registrations that the email
      should handle


Email Sender
------------
Found by viewing an EM Event, then selecting Event Manager -> Email Sender from
the page menu.

The primary purpose of this form is to send emails to a list of registrations.
EMail addresses not pertaining to a registration can be manually entered into
the 'EMail Addressess to Send EMail To' field.

Up to 4 attachments can also be included in the email.


Registration Status
-------------------
Found by viewing an EM Event, then selecting Event Manager -> Registration
Status from the page menu.

The primary purpose of this form is to allow a Manager to approve, confirm,
deny, or cancel registrations, along with moving them back to the waiting
list, if necessary.


Export Registrations
--------------------
Found by viewing an EM Event, then selecting the Event Manager -> Export
Registrations option from the page menu.

The purpose of this feature is to export a list of all registrations along
with all attributes to a CSV file, which should be readable by spreadsheet
software like Excel.


Roster
------
Found by viewing an EM Event, then selecting the Event Manager -> Roster
option from the page menu.

The purpose of this page is to show a list of registrations for the event
on a particular day, and to be able to mark whether or not a particular
registration was in attendance.

It also allows a manager to send printable rosters for each day, if desired.


Certificates
------------
Found by viewing an EM Event, then selecting the Event Manager -> Certificates
option from the page menu.

The purpose of this page is to be able to generate a PDF containing
certificates, one per page, for all registrations that participated in the
EM Event.
