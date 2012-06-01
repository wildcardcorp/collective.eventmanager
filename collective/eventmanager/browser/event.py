from datetime import timedelta
from persistent.dict import PersistentDict
from five import grok

from Products.CMFCore.utils import getToolByName
from collective.geo.mapwidget.browser.widget import MapWidget
from plone.protect import protect, CheckAuthenticator
from persistent.dict import PersistentDict
from zope.annotation.interfaces import IAnnotations

from collective.eventmanager.event import IEMEvent
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager.emailtemplates import sendEMail
from collective.eventmanager.utils import findRegistrationObject
from collective.eventmanager.event import EventSettings


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    MAP_CSS_CLASS = 'eventlocation'

    def __call__(self):
        # setup map widget
        portal = getToolByName(self.context, "portal_url")
        mw = MapWidget(self, self.request, portal)
        mw.mapid = self.MAP_CSS_CLASS
        mw.addClass(self.MAP_CSS_CLASS)
        self.mapfields = [mw]

        return super(View, self).__call__()

    @property
    def number_registered(self):
        # XXX Optimize! catalog
        registrationfolder = self.context.registrations
        wftool = getToolByName(self.context, "portal_workflow")
        count = 0
        for reg in registrationfolder.objectValues():
            status = wftool.getStatusOf(
                "collective.eventmanager.Registration_workflow", reg)
            if status['review_state'] in ('approved', 'confirmed'):
                count += 1
        return count

    @property
    def number_wait_list(self):
        # XXX Optimize! catalog
        registrationfolder = self.context.registrations
        wftool = getToolByName(self.context, "portal_workflow")
        count = 0
        for reg in registrationfolder.objectValues():
            status = wftool.getStatusOf(
                "collective.eventmanager.Registration_workflow", reg)
            if status['review_state'] in ('submitted',):
                count += 1
        return count

    @property
    def reg(self):
        return findRegistrationObject(self.context)

    @property
    def registered(self):
        if self.reg is None:
            return False
        return True

    @property
    def waiting_list(self):
        if self.reg is None:
            return False
        wftool = getToolByName(self.context, "portal_workflow")
        status = wftool.getStatusOf(
            "collective.eventmanager.Registration_workflow",
            self.reg)
        return status['review_state'] != 'approved'

    def cgmapSettings(self):
        settings = {}

        coords = [0, 0]
        if self.context.location != None \
                and self.context.location[0:6] == u'POINT(':
            coords = self.context.location[6:-1].split(' ')

        settings['lon'] = float(coords[0])
        settings['lat'] = float(coords[1])
        settings['zoom'] = 16

        return "cgmap.state['" + self.MAP_CSS_CLASS + "'] = " \
               + str(settings) + ";"


class EMailSenderForm(grok.View):
    """Presents a page that allows an event admin to send out
       registraiton and confirmation emails manually"""
    grok.context(IEMEvent)
    grok.require('cmf.ModifyPortalContent')
    grok.name('emailsenderform')
    grok.layer(ILayer)

    def __call__(self):
        self.emailSent = False
        if self.request.form is not None \
                and len(self.request.form) > 0 \
                and 'submit' in self.request.form:

            self._handlePost(self.request)

        return super(EMailSenderForm, self).__call__()

    @protect(CheckAuthenticator)
    def _handlePost(self, REQUEST=None):
        emailtype = REQUEST.form['emailtype']
        tolist = REQUEST.form['emailtoaddresses'].splitlines()
        attachments = []
        if REQUEST.form['attachment1'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment1'].filename,
                'data': REQUEST.form['attachment1'].read()})
        if REQUEST.form['attachment2'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment2'].filename,
                'data': REQUEST.form['attachment2'].read()})
        if REQUEST.form['attachment3'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment3'].filename,
                'data': REQUEST.request.form['attachment3'].read()})
        if REQUEST.form['attachment4'].filename != '':
            attachments.append({
                'name': REQUEST.form['attachment4'].filename,
                'data': REQUEST.form['attachment4'].read()})
        mfrom = REQUEST.form['emailfromaddress']
        msubject = REQUEST.form['emailsubject']
        mbody = REQUEST.form['emailbody']
        sendEMail(self.__parent__, emailtype, tolist, None, attachments,
                  mfrom, msubject, mbody)

        self.emailSent = True

    def registrationEMailList(self):
        regfolder = self.__parent__.registrations
        return ''.join(["\"%s\" <%s>\n"
                           % (regfolder[reg].title, regfolder[reg].description)
                       for reg in regfolder])

    def showMessageEMailSent(self):
        if getattr(self, 'emailSent', None) != None:
            return self.emailSent

        return False

    def confirmationFrom(self):
        return self.__parent__.thankYouEMailFrom

    def confirmationSubject(self):
        return self.__parent__.thankYouEMailSubject

    def confirmationBody(self):
        return self.__parent__.thankYouEMailBody


class RegistrationStatusForm(grok.View):
    """Creates a form that an event adminsitrator can manage registrations
    currently on the waiting list"""

    grok.context(IEMEvent)
    grok.require('cmf.ModifyPortalContent')
    grok.name('registrationstatusform')
    grok.layer(ILayer)

    def __call__(self):
        if self.request.form is not None \
                and len(self.request.form) > 0 \
                and 'submit' in self.request.form:

            self._handlePost(self.request)

        return super(RegistrationStatusForm, self).__call__()

    @protect(CheckAuthenticator)
    def _handlePost(self, REQUEST):
        subtype = REQUEST.form['submit']
        idlist_submitted = self._getActionsFor('submitted', REQUEST)
        idlist_approved = self._getActionsFor('approved', REQUEST)
        idlist_confirmed = self._getActionsFor('confirmed', REQUEST)
        idlist_cancelled = self._getActionsFor('cancelled', REQUEST)
        idlist_denied = self._getActionsFor('denied', REQUEST)

        if subtype == 'Wait List':
            self._doActions(idlist_approved, ['cancel', 'modify'])
            self._doActions(idlist_confirmed, ['cancel', 'modify'])
            self._doActions(idlist_cancelled, ['modify'])
            self._doActions(idlist_denied, ['modify'])
        elif subtype == 'Approve':
            sendm = self.__parent__.sendOffWaitingListEMail
            self._doActions(idlist_submitted, ['approve'], sendm)
            self._doActions(idlist_confirmed, ['cancel', 'approve'])
            self._doActions(idlist_cancelled, ['approve'])
            self._doActions(idlist_denied, ['approve'])
        elif subtype == 'Confirm':
            sendm = self.__parent__.sendOffWaitingListEMail
            self._doActions(idlist_submitted, ['approve', 'confirm'], sendm)
            self._doActions(idlist_approved, ['confirm'])
            self._doActions(idlist_cancelled, ['approve', 'confirm'])
            self._doActions(idlist_denied, ['approve', 'confirm'])
        elif subtype == 'Cancel':
            self._doActions(idlist_submitted, ['cancel'])
            self._doActions(idlist_approved, ['cancel'])
            self._doActions(idlist_confirmed, ['cancel'])
            self._doActions(idlist_denied, ['cancel'])
        elif subtype == 'Deny':
            self._doActions(idlist_submitted, ['deny'])
            self._doActions(idlist_approved, ['deny'])
            self._doActions(idlist_confirmed, ['deny'])
            self._doActions(idlist_cancelled, ['deny'])
            pass

    def _getActionsFor(self, actiontype, REQUEST):
        if actiontype in REQUEST.form:
            if type(REQUEST.form[actiontype]) == list:
                return REQUEST.form[actiontype]
            else:
                return [REQUEST.form[actiontype]]

        return []

    def _doActions(self, idlist=[], actions=[], sendwaitlistemail=False):
        for id in idlist:
            reg = self.__parent__.registrations[id]
            wf = getToolByName(reg, "portal_workflow")
            for action in actions:
                wf.doActionFor(reg, action)
            if sendwaitlistemail:
                mfrom = self.__parent__.waitingListEMailFrom
                mto = reg.description
                msubject = self.__parent__.offWaitingListEMailSubject
                mbody = self.__parent__.offWaitingListEMailBody
                mh = getToolByName(self.__parent__, 'MailHost')
                mh.send(mbody, mto, mfrom, msubject)

    def getRegistrationsWithStatus(self, status):
        wf = getToolByName(self, 'portal_workflow')
        wfstr = "collective.eventmanager.Registration_workflow"
        items = [r for r in self.__parent__.registrations]
        registrations = []
        for reg in items:
            regstatus = wf.getStatusOf(wfstr,
                                       self.__parent__.registrations[reg])
            reviewstate = regstatus['review_state']
            if reviewstate != None \
                    and reviewstate.lower() == status.lower():
                registrations.append(self.__parent__.registrations[reg])

        return registrations


class EventRoster(grok.View):
    """A printable report for listing all registrations for the event"""

    grok.context(IEMEvent)
    grok.require('cmf.ModifyPortalContent')
    grok.name('eventroster')
    grok.layer(ILayer)

    def initsettings(self):
        self.settings = EventSettings(self.context)
        if self.settings.eventAttendance is None:
            self.settings.eventAttendance = PersistentDict()

    def __call__(self):
        return super(EventRoster, self).__call__()

    def eventDates(self):
        datediff = (self.context.end - self.context.start).days
        return [(self.context.start + timedelta(days=a))
                    for a in range(datediff)]

    def toggleAttendanceState(self):
        postitems = self.request.form.items()
        regdate = None
        regname = None
        for i in range(len(postitems)):
            if postitems[i][0] == 'dt':
                regdate = postitems[i][1]
            elif postitems[i][0] == 'reg':
                regname = postitems[i][1]

        key = regname + ',' + regdate
        self.initsettings()
        if key in self.settings.eventAttendance:
            self.settings.eventAttendance[key] = not self.settings[key]
        else:
            self.settings.eventAttendance[key] = True

    def getCheckedValue(self, reg, dt):
        self.initsettings()
        key = reg + ',' + dt
        if key in self.settings.eventAttendance:
            return 'checked'
        else:
            return ''
