from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ITravelAccommodationFolder(form.Schema):
    """A container for Travel Accommodation objects"""


class View(grok.View):
    """Default view (called "@@view"") for a Travel Accommodation Folder.

    The associated template is found in
    travelaccommodationfolder_templates/view.pt
    """

    grok.context(ITravelAccommodationFolder)
    grok.require('zope2.View')
    grok.name('view')
