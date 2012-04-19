from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ISession(form.Schema):
    """A session within an event"""

    startdate = schema.Datetime(
            title=_("Start Date/Time"),
            description=_("Date and time the session starts"),
            required=True,
        )

    enddate = schema.Datetime(
            title=_("End Date/Time"),
            description=_("Date and time the session ends"),
            required=True,
        )


class View(grok.View):
    """Default view (called "@@view"") for a session.

    The associated template is found in session_templates/view.pt
    """

    grok.context(ISession)
    grok.require('zope2.View')
    grok.name('view')
