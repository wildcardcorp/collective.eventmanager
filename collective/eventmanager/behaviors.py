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

    name = schema.TextLine(
            title=_(u"Test Field [Title]"),
        )
    email = schema.Text(
            title=_(u"Test Field [Description]"),
        )

alsoProvides(IRegistrationFields, form.IFormFieldProvider)


class RegistrationFields(object):
    implements(IRegistrationFields)
    adapts(IDublinCore)

    def __init__(self, context):
        self.context = context

    @getproperty
    def name(self):
        return "HARD CODED NAME"

    @setproperty
    def name(self, value):
        pass

    @getproperty
    def email(self):
        return "HARD CODED EMAIL"

    @setproperty
    def email(self, value):
        pass
