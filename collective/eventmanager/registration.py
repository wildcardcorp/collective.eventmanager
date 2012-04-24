from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistration(form.Schema):
    """A registration for an event"""

    title = schema.TextLine(
            title=_(u"Name"),
            required=True,
        )

    description = schema.TextLine(
            title=_(u"EMail"),
            required=True,
        )


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in registration_templates/view.pt
    """

    grok.context(IRegistration)
    grok.require('zope2.View')
    grok.name('view')
