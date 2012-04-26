from rwproperty import getproperty, setproperty
from plone.directives import form
from zope import schema
from zope.interface import implements, alsoProvides
from zope.component import adapts
#from plone.app.dexterity.behaviors.metadata import IBasic
from Products.CMFCore.interfaces import IDublinCore
#from plone.supermodel import model

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistrationFields(form.Schema):
    """Add fields based on parent EM Event Registration Fields field :)"""

    title = schema.TextLine(
            title=_(u"Name"),
        )
    description = schema.Text(
            title=_(u"EMail Address"),
        )

alsoProvides(IRegistrationFields, form.IFormFieldProvider)


class RegistrationFields(object):
    implements(IRegistrationFields)
    #adapts(IDublinCore)

    def __init__(self, context):
        self.context = context

    @getproperty
    def title(self):
        return "HARD CODED NAME"

    @setproperty
    def title(self, value):
        pass

    @getproperty
    def description(self):
        return "HARD CODED EMAIL"

    @setproperty
    def description(self, value):
        pass
