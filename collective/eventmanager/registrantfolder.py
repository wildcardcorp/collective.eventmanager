from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistrantFolder(form.Schema):
    """A container for Registrant objects"""


class View(grok.View):
    """Default view (called "@@view"") for a Registrant Folder.

    The associated template is found in registrantfolder_templates/view.pt
    """

    grok.context(IRegistrantFolder)
    grok.require('zope2.View')
    grok.name('view')
