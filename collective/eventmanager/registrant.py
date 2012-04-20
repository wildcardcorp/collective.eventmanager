from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


def registrantFormGen(context):
    """Adds the appropriate fields to generate a Registrant from a PloneFormGen
    Form"""

    # NAME
    context.invokeFactory('FormStringField', 'name')
    field = context['name']
    field.setTitle("Name")
    field.setDescription("Please enter your full name")

    # EMAIL ADDRESS
    context.invokeFactory('FormStringField', 'email')
    field = context['email']
    field.setTitle("EMail Address")
    field.setDescription("Please enter a valid email address you can be "
                            + "contacted with")


class IRegistrant(form.Schema):
    """An individual who has registered for an event"""


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IRegistrant)
    grok.require('zope2.View')
    grok.name('view')
