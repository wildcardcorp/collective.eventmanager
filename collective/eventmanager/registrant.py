from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistrant(form.Schema):
    """An individual who has registered for an event"""


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IRegistrant)
    grok.require('zope2.View')
    grok.name('view')
