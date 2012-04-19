from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ILodgingAccommodation(form.Schema):
    """An accomodation made for lodging during the event"""


class View(grok.View):
    """Default view (called "@@view"") for a travel accommodation.

    The associated template is found in lodgingaccommodation_templates/view.pt
    """

    grok.context(ILodgingAccommodation)
    grok.require('zope2.View')
    grok.name('view')
