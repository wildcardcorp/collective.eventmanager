from five import grok
from zope import schema
from plone.directives import form

from collective.eventmanager import EventManagerMessageFactory as _


class ISessionFolder(form.Schema):
    """A container for Session objects"""


class View(grok.View):
    """Default view (called "@@view"") for a Session Folder.

    The associated template is found in sessionfolder_templates/view.pt
    """

    grok.context(ISessionFolder)
    grok.require('zope2.View')
    grok.name('view')
