from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class IEvent(form.Schema):
    """This represents an event
    """

    name = schema.TextLine(
            title=_(u"Name"),
            description=_(u"The name of the event"),
            required=True,
        )
