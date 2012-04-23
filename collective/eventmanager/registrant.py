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

    # CUSTOM SCRIPT ADAPTER
    # Saves results
    context.invokeFactory('FormCustomScriptAdapter', 'registrantsaver')
    field = context['registrantsaver']
    field.setTitle("Save Registrant")
    field.setScriptBody("""
target = context.aq_inner.aq_parent.aq_parent.Registrants
form = request.form
from DateTime import DateTime
uid = str(DateTime().millis())
target.invokeFactory('collective.eventmanager.Registrant',
                     id=uid,
                     title=form['name'])
obj = target[uid]
obj.setDescription(form['email'])
obj.reindexObject()""")


class IRegistrant(form.Schema):
    """An individual who has registered for an event"""


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IRegistrant)
    grok.require('zope2.View')
    grok.name('view')
