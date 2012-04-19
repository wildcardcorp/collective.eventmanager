from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ITravelAccommodation(form.Schema):
    """An accomodation made for traveling"""


class View(grok.View):
    """Default view (called "@@view"") for a travel accommodation.

    The associated template is found in travelaccommodation_templates/view.pt
    """

    grok.context(ITravelAccommodation)
    grok.require('zope2.View')
    grok.name('view')
