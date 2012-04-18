from five import grok
from zope import schema
from plone.directives import form

from collective.conferencemanager import ConferenceManagerMessageFactory as _


class IConference(form.Schema):
    """This represents a conference
    """

    name = schema.TextLine(
            title=_(u"Name"),
            description=_(u"The name of the conference")
        )
