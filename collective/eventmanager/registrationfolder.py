from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistrationFolder(form.Schema):
    """A container for Registration objects"""


class View(grok.View):
    """Default view (called "@@view"") for a Registration Folder.

    The associated template is found in registrationfolder_templates/view.pt
    """

    grok.context(IRegistrationFolder)
    grok.require('zope2.View')
    grok.name('view')
