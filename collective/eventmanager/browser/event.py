from datetime import datetime, timedelta
import re
from persistent.dict import PersistentDict
from mako.template import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from five import grok
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from collective.geo.mapwidget.browser.widget import MapWidget
from plone.protect import protect, CheckAuthenticator
from plone.memoize.view import memoize

from collective.eventmanager.event import IEMEvent
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager.emailtemplates import sendEMail
from collective.eventmanager.utils import findRegistrationObject
from collective.eventmanager.browser.rostersettings import RosterSettings


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in event_templates/view.pt
    """
    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    MAP_CSS_CLASS = 'eventlocation'

    filter_material_paths = (
        'sessions',
        'session-calendar',
        'registrations',
        'travel-accommodations',
        'lodging-accommodations')

    def __call__(self):
        # setup map widget
        portal = getToolByName(self.context, "portal_url")
        mw = MapWidget(self, self.request, portal)
        mw.mapid = self.MAP_CSS_CLASS
        mw.addClass(self.MAP_CSS_CLASS)
        self.mapfields = [mw]

        return super(View, self).__call__()

    @property
    @memoize
    def catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    @memoize
    def number_registered(self):
        return len(self.catalog(path={
            'query': '/'.join(self.context.getPhysicalPath()),
            'depth': 5},
            portal_type="collective.eventmanager.Registration",
            review_state=('approved', 'confirmed')))

    @property
    @memoize
    def number_wait_list(self):
        return len(self.catalog(path={
            'query': '/'.join(self.context.getPhysicalPath()),
            'depth': 5},
            portal_type="collective.eventmanager.Registration",
            review_state=('submitted',)))

    @property
    @memoize
    def reg(self):
        return findRegistrationObject(self.context)

    @property
    def can_register(self):
        if self.context.enableWaitingList:
            return True
        return self.number_registered < self.context.maxRegistrations

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

    @property
    def featured_material(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        return catalog(Subject='featured', path={
            'query': '/'.join(self.context.getPhysicalPath()),
            'depth': 5})

    @property
    def all_material(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        base = '/'.join(self.context.getPhysicalPath())
        filter_material_paths_re = re.compile('^(%s)' % (
            '|'.join([base + '/' + p for p in self.filter_material_paths])))

        res = []
        brains = catalog(path={'query': base + '/', 'depth': 5})
        for brain in brains:
            path = brain.getPath()
            if path != base and not filter_material_paths_re.match(path):
                res.append(brain)
        return res

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

    def registrationEMailListNoShows(self):
        regfolder = self.__parent__.registrations
        return '"' + ''.join(['\\"%s\\" <%s>\\n'
                        % (regfolder[reg].title, regfolder[reg].email)
                    for reg in regfolder
                     if regfolder[reg].noshow]) + '";'

    def registrationEMailList(self, filtered=False):
        regfolder = self.__parent__.registrations

        # return all email addresses formatted for a text field
        if not filtered:
            return '"' + ''.join(['\\"%s\\" <%s>\\n'
                           % (regfolder[reg].title, regfolder[reg].email)
                       for reg in regfolder]) + '";'

        # if there are no attendance settings for the context, then
        # return all email addresses formatted for a text field
        settings = RosterSettings(self.context, IEMEvent)
        if settings.eventAttendance is None:
            return '"' + ''.join(['\\"%s\\" <%s>\\n'
                           % (regfolder[reg].title, regfolder[reg].email)
                       for reg in regfolder]) + '";'

        # get all the days an event is lasting
        datediff = (self.context.end - self.context.start).days
        evdates = [(self.context.start + timedelta(days=a))
                    for a in range(datediff)]
        # for each registration, see if there are any days that have an
        # attendance record and add it to a list if non are found
        noattendance = []
        for r in regfolder:
            found = False
            for dt in evdates:
                key = "%s,%s" % (r, dt.strftime('%m/%d/%Y'))
                if key in settings.eventAttendance:
                    found = True
                    break
            if not found:
                noattendance.append(r)
        # return list of emails addresses formated for a text field
        return '"' + ''.join(['\\"%s\\" <%s>\\n'
                        % (regfolder[reg].title, regfolder[reg].email)
                    for reg in noattendance]) + '";'

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


class EventRosterView(BrowserView):
    """A report for listing all registrations for an event or session.
    also provides an attendance checklist."""

    use_interface = IEMEvent

    def makeDictFromPost(self, ints=[]):
        """
            'ints' is an array of strings that are key values in
            the form post variables that should have their associated
            values converted to integers. If a value cannot be
            converted, it is set to None.
        """
        items = self.request.form.items()
        values = {}
        for i in range(len(items)):
            if items[i][0] in ints:
                try:
                    values[items[i][0]] = int(items[i][1])
                except ValueError:
                    values[items[i][0]] = None
            else:
                values[items[i][0]] = items[i][1]

        return values

    def initsettings(self):
        self.settings = RosterSettings(self.context, self.use_interface)
        if self.settings.eventAttendance is None:
            self.settings.eventAttendance = PersistentDict()

    def eventDates(self):
        datediff = (self.context.end - self.context.start).days
        return [(self.context.start + timedelta(days=a))
                    for a in range(datediff)]

    def hasNoShow(self):
        for item in self.context.registrations:
            if self.context.registrations[item].noshow:
                return True

        return False

    def noShows(self):
        return [a for a in self.context.registrations
                   if self.context.registrations[a].noshow]

    def toggleAttendanceState(self):
        postitems = self.makeDictFromPost()
        regdate = postitems['dt']
        regname = postitems['reg']

        key = regname + ',' + regdate
        self.initsettings()
        #import pdb; pdb.set_trace()
        if key in self.settings.eventAttendance:
            self.settings.eventAttendance[key] = \
                    not self.settings.eventAttendance[key]
        else:
            self.settings.eventAttendance[key] = True

    def getCheckedValue(self, reg, dt):
        self.initsettings()
        key = reg + ',' + dt
        #import pdb; pdb.set_trace()
        if key in self.settings.eventAttendance \
                and self.settings.eventAttendance[key]:
            return 'checked'
        else:
            return ''

    def emailRoster(self):
        postitems = self.makeDictFromPost()

        if 'to' not in postitems or postitems['to'] == None \
                or postitems['to'] == '':
            return "no to address"
        if 'from' not in postitems or postitems['from'] == None \
                or postitems['from'] == '':
            return "no to address"
        elif 'text' not in postitems or postitems['text'] == None \
                or postitems['text'] == '':
            postitems['text'] = ''

        registry = getUtility(IRegistry)
        subject = registry.records['collective.eventmanager.emailtemplates.IEMailTemplateSettings.roster_subject'].value
        htmlmessage = registry.records['collective.eventmanager.emailtemplates.IEMailTemplateSettings.roster_htmlbody'].value
        plainmessage = registry.records['collective.eventmanager.emailtemplates.IEMailTemplateSettings.roster_textbody'].value
        if subject == None:
            subject = 'Roster for ' + self.context.title
        if htmlmessage == None:
            htmlmessage = ''
        if plainmessage == None:
            plainmessage = ''

        htmlmessage += '<div>' + postitems['text'] + '</div>'
        plainmessage += '\n\n' + postitems['text']

        regs = [self.context.registrations[a]
                    for a in self.context.registrations]

        subjecttemplate = Template(subject)
        htmltemplate = Template(htmlmessage)
        plaintemplate = Template(plainmessage)
        renderedsubject = subjecttemplate.render(emevent=self.context,
                                                 registrations=regs)
        renderedhtml = htmltemplate.render(emevent=self.context,
                                           registrations=regs)
        renderedplain = plaintemplate.render(emevent=self.context,
                                           registrations=regs)

        mh = getToolByName(self.context, 'MailHost')
        msg = MIMEMultipart('alternative')
        msgpart1 = MIMEText(renderedplain, 'plain')
        msgpart2 = MIMEText(renderedhtml, 'html')
        msg.attach(msgpart1)
        msg.attach(msgpart2)
        msg['Subject'] = renderedsubject
        msg['From'] = postitems['from']
        msg['To'] = postitems['to']
        try:
            mh.send(msg)
        except Exception:
            return 'failure'

        return 'success'


class ExportRegistrationsView(BrowserView):
    def exportRegistrations(self):
        filename = "registrations-%s.csv" \
                        % (datetime.now().strftime('%m-%d-%Y'))
        self.request.response.setHeader('Content-Type',
                                        'text/plain')
        self.request.response.setHeader('Content-Disposition',
                                        'attachment; filename="%s"'
                                            % (filename,))

        cvsout = '"Name","EMail","Is No Show?"'
        # generate header row
        fields = []
        for fielddata in self.context.registrationFields:
            fields.append(fielddata['name'])
            cvsout += ',"%s"' % (fielddata['name'].replace('"', '""'),)
        cvsout += "\n"

        # get values for all the registrations
        for regname in self.context.registrations:
            reg = self.context.registrations[regname]

            name = reg.title
            email = reg.email
            noshow = ''
            if email is None:
                email = ''
            if reg.noshow:
                noshow = 'Yes'
            cvsout += '"%s","%s","%s"' % (name.replace('"', '""'),
                                          email.replace('"', '""'),
                                          noshow)
            for field in fields:
                try:
                    val = getattr(reg, field)
                except AttributeError:
                    val = ''
                cvsout += ',"%s"' % (val.replace('"', '""'))

            cvsout += "\n"

        self.request.response.setBody(cvsout)
