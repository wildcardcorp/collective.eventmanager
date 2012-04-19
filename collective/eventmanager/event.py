from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class IEMEvent(form.Schema):
    """An event"""

    startdate = schema.Datetime(
            title=_("Start Date/Time"),
            description=_("Date and time the Event starts"),
            required=True,
        )

    enddate = schema.Datetime(
            title=_("End Date/Time"),
            description=_("Date and time the Event ends"),
            required=True,
        )


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('view')
