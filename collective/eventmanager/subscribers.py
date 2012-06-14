from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.interface import alsoProvides

from five import grok

from Products.CMFCore.utils import getToolByName
from Products.PloneGetPaid.interfaces import IBuyableMarker

from collective.eventmanager.event import IEMEvent
from collective.eventmanager.registration import IRegistration
from collective.eventmanager.utils import getNumApprovedAndConfirmed
from collective.eventmanager.config import BASE_TYPE_NAME
from collective.eventmanager.emailtemplates import sendEMail


def _canAdd(folder, type_name):
    folder.setConstrainTypesMode(1)
    folder.setLocallyAllowedTypes((BASE_TYPE_NAME + type_name,))


def _addSessionsFolder(emevent):
    # add a folder to hold sessions
    id = emevent.invokeFactory('Folder', 'sessions', title="Sessions")
    _canAdd(emevent[id], 'Session')


def _addSessionCalender(emevent):
    # Add a collections object for a calendar if available.
    idval = emevent.invokeFactory('Topic', 'session-calendar',
                                  title="Session Calendar")
    sessioncal = emevent[idval]
    criterion = sessioncal.addCriterion('Type', 'ATPortalTypeCriterion')
    criterion.setValue('Session')
    criterion = sessioncal.addCriterion('path', 'ATRelativePathCriterion')
    criterion.setRelativePath('../sessions')
    sessioncal.setLayout('solgemafullcalendar_view')


@grok.subscribe(IEMEvent, IObjectAddedEvent)
def addFoldersForEventFormsFolder(emevent, event):
    """Adds the forms and folders required for an emevent"""

    # make buyable
    alsoProvides(emevent, IBuyableMarker)

    # add session container and a session calendar
    if emevent.enableSessions:
        if 'sessions' not in emevent.objectIds():
            _addSessionsFolder(emevent)
        if 'session-calendar' not in emevent.objectIds():
            _addSessionCalender(emevent)

    id = emevent.invokeFactory(
                        'Folder',
                        'registrations',
                        title='Registrations')
    _canAdd(emevent[id], 'Registration')

    # add a folder to hold travel accommodations
    id = emevent.invokeFactory(
                        'Folder',
                        'travel-accommodations',
                        title='Travel Accommodations')
    _canAdd(emevent[id], 'Accommodation')

    # add a folder to hold lodging accommodations
    id = emevent.invokeFactory(
                        'Folder',
                        'lodging-accommodations',
                        title='Lodging Accommodations')
    _canAdd(emevent[id], 'Accommodation')

    # add a folder to hold news items for event announcments
    id = emevent.invokeFactory(
                        'Folder',
                        'announcements',
                        title='Announcements')
    emevent[id].setConstrainTypesMode(1)
    emevent[id].setLocallyAllowedTypes(('News Item',))


@grok.subscribe(IEMEvent, IObjectModifiedEvent)
def checkEventForSessionsState(emevent, event):
    """If sessions are disabled then remove the sessions folder,
       they are enabled, then session folders should be added."""
    ids = emevent.objectIds()
    if not emevent.enableSessions:
        if 'sessions' in ids:
            emevent.manage_delObjects(['sessions'])
        if 'session-calendar' in ids:
            emevent.manage_delObjects(['session-calendar'])
    else:
        if 'sessions' not in ids:
            _addSessionsFolder(emevent)
        if 'session-calendar' not in ids:
            _addSessionCalender(emevent)


@grok.subscribe(IRegistration, IObjectAddedEvent)
def handleNewRegistration(reg, event):
    parentevent = reg.__parent__.__parent__
    regfolderish = reg.__parent__
    # first, check if the user needs to be created
    user = getToolByName(reg, 'acl_users').getUserById(reg.email)
    if not user:
        # create member and make him owner of registration object
        regtool = getToolByName(reg, 'portal_registration')
        member = regtool.addMember(reg.email, regtool.generatePassword(),
            properties={
                'fullname': reg.title, 'email': reg.email,
                'username': reg.email
            })
        # should we do a different email than password reset?
        # more like, hey, can account was create, set your password!
        regtool.mailPassword(reg.email, reg.REQUEST)
        user = member.getUser()
    reg.manage_setLocalRoles(reg.email, ["Owner"])
    # Make sure user is owner of this sucker
    reg.reindexObjectSecurity()

    hasWaitingList = parentevent.enableWaitingList
    hasPrivateReg = parentevent.privateRegistration
    maxreg = parentevent.maxRegistrations
    numRegApproved = getNumApprovedAndConfirmed(regfolderish)

    workflowTool = getToolByName(reg, "portal_workflow")

    # private registration means manual adding of registrations
    if hasPrivateReg:
        workflowTool.doActionFor(reg, 'approve')
    # haven't hit max, 'approve'
    elif maxreg == None or numRegApproved < maxreg:
        workflowTool.doActionFor(reg, 'approve')
        sendEMail(parentevent, 'thank you', [reg.email], reg)
    # waiting list, and hit max == remain 'submitted' (on waiting list)
    elif hasWaitingList:
        sendEMail(parentevent, 'on waiting list', [reg.email], reg)
    # all other cases, 'deny'
    else:
        workflowTool.doActionFor(reg, 'deny')
        sendEMail(parentevent, 'registration full', [reg.email], reg)
