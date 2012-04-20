from five import grok
from zope import schema
from plone.directives import form

from plone.app.textfield import RichText

from collective.eventmanager import EventManagerMessageFactory as _


class ISession(form.Schema):
    """A session within an event"""

    name = schema.TextLine(
            title=_(u"Name of Session"),
            description=_(u"Name of session displayed to users"),
            required=True,
        )

    description = RichText(
            title=_(u"Description/Notes"),
            description=_(u"A description or notes about the session"),
            required=False,
        )

    startdate = schema.Datetime(
            title=_(u"Start Date/Time"),
            description=_(u"Date and time the session starts"),
            required=True,
        )

    enddate = schema.Datetime(
            title=_(u"End Date/Time"),
            description=_(u"Date and time the session ends"),
            required=True,
        )

    maxParticipants = schema.Int(
            title=_(u"Maximum Participants"),
            description=_(u"The maximum number of registrants that can "
                            + u"participate in this session"),
            required=True,
        )

    # === CONTACT/PRESENTER DETAILS ===
    contactName = schema.TextLine(
            title=_(u"Contact/Presenter Name"),
            description=_(u"A name for the primary contact or presenter of "
                            + u"this event"),
            required=False,
        )

    contactDetails = RichText(
            title=_(u"Contact/Presenter Details"),
            description=_(u"Put information about the contact/presentor, "
                            + u"including phone, email, twitter handle, and "
                            + u"any other descriptive information about the "
                            + u"person"),
            required=False,
        )


class View(grok.View):
    """Default view (called "@@view"") for a session.

    The associated template is found in session_templates/view.pt
    """

    grok.context(ISession)
    grok.require('zope2.View')
    grok.name('view')
