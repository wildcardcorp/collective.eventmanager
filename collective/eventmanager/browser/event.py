from datetime import datetime, timedelta
from DateTime import DateTime
import re
from persistent.dict import PersistentDict
from mako.template import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from collective.geo.mapwidget.browser.widget import MapWidget
from five import grok
from plone.directives import form
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.view import memoize
from plone.protect import protect
from plone.protect import CheckAuthenticator
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.interfaces import IErrorViewSnippet
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility

from collective.eventmanager import EventManagerMessageFactory as _
from collective.eventmanager.browser.registration import addDynamicFields
from collective.eventmanager.browser.rostersettings import RosterSettings
from collective.eventmanager.certificatepdftemplates \
    import generateCertificate
from collective.eventmanager.certificatepdftemplates \
    import getDefaultValueForCertField
from collective.eventmanager.emailtemplates import sendEMail
from collective.eventmanager.event import IEMEvent
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager.registration import IRegistration
from collective.eventmanager.registration import generateRegistrationHash
from collective.eventmanager.utils import findRegistrationObject


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
        'lodging-accommodations',
        'announcements')

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
    def can_register(self):
        # check to make sure registration is still open
        if self.context.registrationOpen > datetime.now() \
                or (self.context.registrationClosed is not None
                    and self.context.registrationClosed <= datetime.now()):
            return False

        # check to see if there are no registration caps
        if self.context.enableWaitingList or \
                self.context.maxRegistrations is None:
            return True

        # check to see if there are still open spots available
        return self.number_registered < self.context.maxRegistrations

    @property
    def can_req_reg_reminder(self):
        return self.context.registrationOpen > datetime.now()

    @property
    def can_pay(self):
        return self.context.requirePayment or self.context.registrationFee

    @property
    def featured_material(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        return catalog(Subject='featured', path={
            'query': '/'.join(self.context.getPhysicalPath()),
            'depth': 5})

    @property
    def all_material(self):
        base = '/'.join(self.context.getPhysicalPath())
        filter_material_paths_re = re.compile('^(%s)' % (
            '|'.join([base + '/' + p for p in self.filter_material_paths])))

        res = []
        brains = self.catalog(path={'query': base + '/', 'depth': 5})
        for brain in brains:
            path = brain.getPath()
            if path != base and not filter_material_paths_re.match(path):
                res.append(brain)
        return res

    @property
    def announcements(self):
        base = '%s/announcements' % '/'.join(self.context.getPhysicalPath())
        limit = 20
        return self.catalog(path={'query': base, 'depth': 5},
                                  sort_on="effective", sort_limit=limit,
                                  portal_type="News Item")[:limit]

    def showMap(self):
        return self.context.location is not None \
                and self.context.location != '' \
                and self.context.location[:6] == 'POINT('

    def cgmapSettings(self):
        settings = {}

        coords = [0, 0]
        if self.context.location != None \
                and self.context.location[0:6] == u'POINT(':
            coords = self.context.location[6:-1].split(' ')

        try:
            settings['lon'] = float(coords[0])
            settings['lat'] = float(coords[1])
            settings['zoom'] = 16
        except ValueError:
            settings['lon'] = 0.0
            settings['lat'] = 0.0
            settings['zoom'] = 1

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

        # get attachments
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

        # if a certificate is requested, then generate the certificate, and add
        # it to the attachment list
        if 'certreq' in REQUEST.form and REQUEST.form['certreq'] == 'on':
            # get registrations
            regs = []
            for r in self.context.registrations:
                reg = self.context.registrations[r]
                for toemail in tolist:
                    if reg.email in toemail:
                        regs.append(reg)
                        break

            # get portal url
            urltool = getToolByName(self.context, 'portal_url')
            portal = urltool.getPortalObject()
            portal_url = portal.absolute_url()

            # get cert info
            certinfo = {}
            for key in ["title", "subtitle", "prenamedesc", "postnamedesc",
                        "awardtitle", "date", "sigdesc", "border"]:
                certinfo['cert%s' % (key,)] = getDefaultValueForCertField(key)

            # get pdf content
            pdf = generateCertificate(registrations=regs,
                                      portal_url=portal_url,
                                      underlines_for_empty_values=False,
                                      **certinfo)

            # add to attachments
            attachments.append({
                    'name': 'certificate.pdf',
                    'data': pdf['file']
                })

        mfrom = REQUEST.form['emailfromaddress']
        msubject = REQUEST.form['emailsubject']
        mbody = REQUEST.form['emailbody']
        for toaddress in tolist:
            # should return a list of one since emails are unique in this
            # system
            reg = [self.__parent__.registrations[a]
                    for a in self.__parent__.registrations
                     if self.__parent__.registrations[a].email in toaddress]
            # if there is no reg, then just send an email with no registration
            # confirmation link, otherwise include the confirmation link (if
            # the event is configured to include one)
            if len(reg) <= 0:
                sendEMail(self.__parent__, emailtype, [toaddress], None,
                          attachments, mfrom, msubject, mbody)
            else:
                sendEMail(self.__parent__, emailtype, [toaddress], reg[0],
                          attachments, mfrom, msubject, mbody)

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

    def confirmationLinkIncluded(self):
        return self.__parent__.thankYouIncludeConfirmation


class ConfirmRegistrationView(grok.View):

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('confirm-registration')
    grok.layer(ILayer)

    confirmed = False

    def __call__(self):
        # TODO: make sure this works...

        regconfirmhash = self.request.get('h')
        # if a match is found, then move it to the confirm state and
        # set a flag for the template to show a 'confirmed' message
        for reg in self.context.registrations:
            reghash = generateRegistrationHash(
                        'confirmation',
                        self.context.registrations[reg])
            if reghash == regconfirmhash:
                self.confirmed = True
                wf = getToolByName(self.context, 'portal_workflow')
                curstatus = wf.getStatusOf(
                              'collective.eventmanager.Registration_workflow',
                              self.context.registrations[reg])
                # only confirm a registration if it has been approved
                if curstatus is not None \
                        and curstatus['review_state'] == 'approved':
                    wf.doActionFor(self.context.registrations[reg], 'confirm')

                break

        return super(ConfirmRegistrationView, self).__call__()


class CancelRegistrationView(grok.View):

    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('cancel-registration')
    grok.layer(ILayer)

    canceled = False

    def __call__(self):
        # TODO: make sure this works...

        regcancelhash = self.request.get('h')
        # if a match is found, then move it to the confirm state and
        # set a flag for the template to show a 'confirmed' message
        for reg in self.context.registrations:
            reghash = generateRegistrationHash(
                        'cancel',
                        self.context.registrations[reg])
            if reghash == regcancelhash:
                self.confirmed = True
                wf = getToolByName(self.context, 'portal_workflow')
                curstatus = wf.getStatusOf(
                              'collective.eventmanager.Registration_workflow',
                              self.context.registrations[reg])
                # only confirm a registration if it has been approved
                if curstatus is not None \
                        and curstatus['review_state'] != 'cancelled' \
                        and curstatus['review_state'] != 'denied':
                    wf.doActionFor(self.context.registrations[reg], 'cancel')

                break

        return super(CancelRegistrationView, self).__call__()


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
        if datediff == 0:
            return [self.context.start]
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
        if key in self.settings.eventAttendance:
            self.settings.eventAttendance[key] = \
                    not self.settings.eventAttendance[key]
        else:
            self.settings.eventAttendance[key] = True

    def getCheckedValue(self, reg, dt):
        self.initsettings()
        key = reg + ',' + dt
        if key in self.settings.eventAttendance \
                and self.settings.eventAttendance[key]:
            return 'checked'
        else:
            return ''

    def emailRoster(self):
        postitems = self.makeDictFromPost()
        tokey = 'event_roster_email_to'
        fromkey = 'event_roster_email_from'
        textkey = 'event_roster_email_text'

        if tokey not in postitems or postitems[tokey] == None \
                or postitems[tokey] == '':
            return "no to address"
        if fromkey not in postitems or postitems[fromkey] == None \
                or postitems[fromkey] == '':
            return "no to address"
        elif textkey not in postitems or postitems[textkey] == None \
                or postitems[textkey] == '':
            postitems[textkey] = ''

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

        htmlmessage += '<div>' + postitems[textkey] + '</div>'
        plainmessage += '\n\n' + postitems[textkey]

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
        msg['From'] = postitems[fromkey]
        msg['To'] = postitems[tokey]
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
                if isinstance(val, list):
                    cvsout += ',"%s"' % (", ".join(val).replace('"', '""'),)
                else:
                    cvsout += ',"%s"' % (val.replace('"', '""'))

            cvsout += "\n"

        self.request.response.setBody(cvsout)


class PublicRegistrationForm(form.SchemaForm):
    grok.context(IEMEvent)
    grok.require('zope2.View')
    grok.name('registration-form')
    grok.layer(ILayer)

    schema = IRegistration
    ignoreContext = True

    MAP_CSS_CLASS = 'eventlocation'

    label = 'Register'

    @property
    def description(self):
        return 'Fill out this form to register for \'' + self.title + '\''

    @button.buttonAndHandler(_('Register'), name='register')
    def handle_register(self, action):
        data, errors = self.extractData()
        if not errors:
            email = data['email']
            reg = findRegistrationObject(self.context, email)
            if reg is not None:
                widget = self.widgets['email']
                view = getMultiAdapter(
                    (schema.ValidationError(),
                     self.request, widget, widget.field,
                     self, self.context), IErrorViewSnippet)
                view.update()
                view.message = u"Duplicate Registration"
                widget.error = view
                errors += (view,)
        if errors:
            self.status = self.formErrorsMessage
            return

        # avoid security checks and add a registration to the
        # registraitons folder of the event
        pt = getToolByName(self, 'portal_types')
        type_info = pt.getTypeInfo('collective.eventmanager.Registration')
        normalizer = getUtility(IIDNormalizer)
        newid = normalizer.normalize(data['title'])
        #import pdb; pdb.set_trace()
        obj = type_info._constructInstance(
                self.context['registrations'],
                type_name='collective.eventmanager.Registration',
                id=newid,
                **data)
        if hasattr(type_info, '_finishConstruction'):
            finobj = type_info._finishConstruction(obj)
        else:
            finobj = obj

        if finobj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            msg = "Registration Complete"
            IStatusMessage(self.request).addStatusMessage(
                msg, "info")

    def updateWidgets(self):
        em = self.context
        for fielddata in em.registrationFields:
            if fielddata['fieldtype'] == 'List':
                self.fields[fielddata['name']].widgetFactory = \
                                                    CheckBoxFieldWidget
                self.fields[fielddata['name']].field.context = self.context

        super(form.SchemaForm, self).updateWidgets()

    def updateFields(self):
        super(form.SchemaForm, self).updateFields()
        em = self.context
        addDynamicFields(self, em.registrationFields)

    def showMap(self):
        return self.context.location is not None \
                and self.context.location != '' \
                and self.context.location[:6] == 'POINT('

    def location(self):
        return self.context.location

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


class EventCertificationView(BrowserView):
    def __call__(self):
        if self.request.form is not None \
                and len(self.request.form) > 0 \
                and 'submit' in self.request.form:

            self._handlePost(self.request)

        return super(EventCertificationView, self).__call__()

    def _handlePost(self, REQUEST=None):
        regs = [self.context.registrations[a]
                    for a in REQUEST.form
                     if a != 'submit' \
                        and a[:4] != 'cert' \
                        and REQUEST.form[a] == 'on']

        certinfo = {}
        for key in ['certtitle', 'certsubtitle', 'certprenamedesc',
                    'certpostnamedesc', 'certawardtitle', 'certdate',
                    'certsigdesc', 'certborder']:
            if key not in REQUEST.form or REQUEST.form[key] == None:
                certinfo[key] = ''
            else:
                certinfo[key] = REQUEST.form[key]

        urltool = getToolByName(self.context, 'portal_url')
        portal = urltool.getPortalObject()
        portal_url = portal.absolute_url()

        pdf = generateCertificate(regs, portal_url, True, **certinfo)

        REQUEST.response.setHeader('Content-Disposition',
                                   'attachment; filename=%s' % pdf['filename'])
        REQUEST.response.setHeader('Content-Type', 'application/pdf')
        REQUEST.response.setHeader('Content-Length', len(pdf['file']))
        REQUEST.response.setHeader('Last-Modified',
                                   DateTime.rfc822(DateTime()))
        REQUEST.response.setHeader('Cache-Control', 'no-store')
        REQUEST.response.setHeader('Pragma', 'no-cache')
        REQUEST.response.write(pdf['file'])

    def getDefaultValue(self, field):
        return getDefaultValueForCertField(field)
