from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ITravelAccommodation(form.Schema):
    """An accomodation made for traveling"""

    location = schema.TextLine(
            title=_(u"Location"),
            description=_(u"Address that will be automatically linked to a "
                            + u"Google Map"),
            required=False,
        )


class View(grok.View):
    """Default view (called "@@view"") for a travel accommodation.

    The associated template is found in travelaccommodation_templates/view.pt
    """

    grok.context(ITravelAccommodation)
    grok.require('zope2.View')
    grok.name('view')
