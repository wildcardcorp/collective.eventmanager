from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ILodgingAccommodationFolder(form.Schema):
    """A container for Lodging Accommodation objects"""


class View(grok.View):
    """Default view (called "@@view"") for a Lodging Accommodation Folder.

    The associated template is found in
    lodgingaccommodationfolder_templates/view.pt
    """

    grok.context(ILodgingAccommodationFolder)
    grok.require('zope2.View')
    grok.name('view')
