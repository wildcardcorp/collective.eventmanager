from zope.component import getMultiAdapter
from zope import schema
from five import grok

from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName
from plone.z3cform.fieldsets import utils
from z3c.form.interfaces import IErrorViewSnippet
from z3c.form import button
from plone.directives import dexterity

from collective.eventmanager.interfaces import ILayer
from collective.eventmanager.utils import getNumApprovedAndConfirmed
from collective.eventmanager.registration import IRegistration
from collective.eventmanager import EventManagerMessageFactory as _


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in registration_templates/view.pt
    """

    grok.context(IRegistration)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    @property
    def event(self):
        return self.context.__parent__.__parent__

    @property
    def review_state(self):
        workflowTool = getToolByName(self.context, "portal_workflow")
        status = workflowTool.getStatusOf(
            "collective.eventmanager.Registration_workflow", self.context)
        return status['review_state']

    @property
    def require_payment(self):
        return self.event.requirePayment and not self.context.paid_fee \
            and self.review_state == 'submitted' and self.room_available

    @property
    def room_available(self):
        event = self.event
        num = getNumApprovedAndConfirmed(self.context)
        if not event.maxRegistrations:
            return True
        return num < event.maxRegistrations

    def dynamicFields(self):
        registrationFields = \
            self.context.__parent__.__parent__.registrationFields
        fields = []
        for fielddata in registrationFields:
            n = fielddata['name']
            t = fielddata['fieldtype']
            try:
                v = getattr(self.context, fielddata['name'])
            except AttributeError:
                v = ''

            fields.append({
                'name': n,
                'fieldtype': t,
                'value': v})

        return fields

    def getDisplayValueFor(self, item):
        if item['value'] == None:
            return ''

        if item['fieldtype'] == 'Bool':
            return 'Yes' if item['value'] else 'No'
        elif item['fieldtype'] == 'URI':
            return "<a href='%s' onclick=\"window.open('%s');return false;\"" \
                   ">%s</a>" % (item['value'], item['value'], item['value'])
        elif item['fieldtype'] == 'Datetime':
            v = item['value']

            timestr = ''
            datestr = ''

            # check if a user entered a date value
            if v.day != 0 or v.month != 0 or v.year != 0:
                datestr = v.strftime('%d/%m/%Y')
            # check if a user entered a time value
            if v.hour != 0 or v.minute != 0:
                timestr = v.strftime('%I:%M%p')

            return datestr + ' ' + timestr
        elif item['fieldtype'] == 'Float':
            # since the type name presented to users is 'Number',
            # if the user entered an integer value, then display
            # an integer value
            if item['value'] % int(item['value']) == 0:
                return int(item['value'])

        return item['value']


def addDynamicFields(form, reg_fields):
    for fielddata in reg_fields:
        field = getattr(schema, fielddata['fieldtype'])(
                    title=unicode(fielddata['name']),
                    required=fielddata['required'])
        field.__name__ = str(fielddata['name'])
        field.interface = IRegistration
        utils.add(form, field)


class EditForm(dexterity.EditForm):
    grok.context(IRegistration)

    def updateWidgets(self):
        super(dexterity.EditForm, self).updateWidgets()
        # can't actually edit these as they can be descructive.
        # should delete and then re-add
        self.widgets['email'].mode = 'display'
        self.widgets['title'].mode = 'display'

    def updateFields(self):
        super(dexterity.EditForm, self).updateFields()
        em = self.context.__parent__.__parent__
        addDynamicFields(self, em.registrationFields)


class AddForm(dexterity.AddForm):
    grok.name('collective.eventmanager.Registration')

    @property
    def label(self):
        if self.userRegistering:
            return u'Register to event'
        else:
            return u'Register user'

    @property
    def description(self):
        if self.userRegistering:
            return u"Register for this event..."
        else:
            return u"You are registering a new user. "

    @property
    def userRegistering(self):
        """
        If the current user is registering. Otherwise, it could be
        an admin signing someone else up.
        """
        return 'current-user' in self.request or \
            self.widgets['for_current_user'].value == 'yes'

    @property
    def member(self):
        mt = getToolByName(self.context, 'portal_membership')
        return mt.getAuthenticatedMember()

    @button.buttonAndHandler(_('Register'), name='register')
    def handle_register(self, action):
        data, errors = self.extractData()
        # XXX before we save, we need to make sure there aren't
        # XXX already registrations for same user.
        # XXX Make faster! Index and use catalog
        if not errors:
            email = data['email']
            for registration in self.context.objectValues():
                if registration.email == email:
                    widget = self.widgets['email']
                    view = getMultiAdapter(
                        (schema.ValidationError(),
                         self.request, widget, widget.field,
                         self, self.context), IErrorViewSnippet)
                    view.update()
                    view.message = u"Duplicate Registration"
                    widget.error = view
                    errors += (view,)
                    break
        if errors:
            self.status = self.formErrorsMessage
            return
        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            if data.get('for_current_user', False):
                msg = u'Registration submitted'
            else:
                msg = u'Registered user'
            IStatusMessage(self.request).addStatusMessage(
                msg, "info")

    def updateWidgets(self):
        super(dexterity.AddForm, self).updateWidgets()
        if self.userRegistering:
            member = self.member
            IStatusMessage(self.request).addStatusMessage(
                u"You are currently logged in and registering as %s." % (
                    self.member.getUserName()), 'info')
            # default to current user name and email
            self.widgets['email'].value = member.getUserName()
            self.widgets['email'].mode = 'display'
            self.widgets['title'].value = member.getProperty('fullname')
            self.widgets['title'].mode = 'display'
            self.widgets['for_current_user'].value = u'yes'

    def updateFields(self):
        super(dexterity.AddForm, self).updateFields()
        em = self.context.__parent__
        addDynamicFields(self, em.registrationFields)
