import os

from five import grok
from plone.z3cform.fieldsets import utils
from plone.directives import dexterity
#from plone.supermodel.model import Fieldset
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName
from z3c.form import button
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.interfaces import IErrorViewSnippet
from zope import schema
from zope.component import getMultiAdapter
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from collective.eventmanager import EventManagerMessageFactory as _
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager.registration import IRegistration
from collective.eventmanager.utils import findRegistrationObject
from collective.eventmanager.utils import getNumApprovedAndConfirmed


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in registration_templates/view.pt
    """

    grok.context(IRegistration)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    enable_form_tabbing = False

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

    @property
    def customContent(self):
        #import pdb; pdb.set_trace()
        if 'CUSTOM_REGISTRATION_CONTENT_TEMPLATE' in os.environ:
            try:
                renderedtemp = ViewPageTemplateFile(
                    os.environ['CUSTOM_REGISTRATION_CONTENT_TEMPLATE'])
                return renderedtemp(self)
            except:
                return ""

        return ""

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
            c = fielddata['configuration']

            fields.append({
                'name': n,
                'fieldtype': t,
                'value': v,
                'config': c})

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
        elif item['fieldtype'] == 'List':
            if len(item['value']) > 0:
                return '<ul><li>%s</li></ul>' \
                            % ("</li><li>".join(item['value']),)
            else:
                return ''

        return item['value']


def addDynamicFields(form, reg_fields):
    # build fieldsets
    found_sets = {}
    for fielddata in reg_fields:
        if fielddata != None and fielddata['fieldset'] != "" and fielddata != "<NO_VALUE>":
            if fielddata['fieldset'] in found_sets:
                found_sets[fielddata['fieldset']].append(fielddata['name'])
            else:
                found_sets[fielddata['fieldset']] = [fielddata['name']]

    counter = 0
    #import pdb; pdb.set_trace()
    for fieldset in found_sets:
        #field = Fieldset("dynamicfieldset%d" % (counter,),
        #                 label=_(fieldset),
        #                 fields=found_sets[fieldset])
        #utils.add(form, field)
        #form.fieldset("dynamicfieldset" + counter,
        #              label=_(fieldset),
        #              fields=found_sets[fieldset])
        counter += 1

    # build fields
    for fielddata in reg_fields:
        kwargs = dict(title=unicode(fielddata['name']),
                      required=fielddata['required'])
        if fielddata['fieldtype'] == 'List':
            vocab = []
            for value in fielddata.get('configuration').splitlines():
                vocab.append(SimpleTerm(value=value, title=value))
            kwargs['value_type'] = schema.Choice(
                                        vocabulary=SimpleVocabulary(vocab))
        field = getattr(schema, fielddata['fieldtype'])(**kwargs)
        field.__name__ = str(fielddata['name'])
        field.interface = IRegistration
        utils.add(form, field)


class EditForm(dexterity.EditForm):
    grok.context(IRegistration)

    enable_form_tabbing = False

    def updateWidgets(self):
        em = self.context.__parent__
        for fielddata in em.registrationFields:
            if fielddata['fieldtype'] == 'List':
                self.fields[fielddata['name']].widgetFactory = \
                                                    CheckBoxFieldWidget
                self.fields[fielddata['name']].field.context = self.context

        super(dexterity.EditForm, self).updateWidgets()

    def updateFields(self):
        super(dexterity.EditForm, self).updateFields()
        #import pdb; pdb.set_trace()
        em = self.context.__parent__.__parent__
        addDynamicFields(self, em.registrationFields)


class AddForm(dexterity.AddForm):
    grok.name('collective.eventmanager.Registration')

    enable_form_tabbing = False

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
        return 'new-user' in self.request or \
            self.widgets['new_user'].value == 'yes'

    @property
    def member(self):
        mt = getToolByName(self.context, 'portal_membership')
        return mt.getAuthenticatedMember()

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
        # when creating a new registration, the no-show value should always
        # be False, but hiding the widget makes it come out True. This just
        # make sure it's set correctly
        data['noshow'] = False
        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            if data.get('new_user', False):
                msg = u'Registration submitted'
            else:
                msg = u'Registered user'
            IStatusMessage(self.request).addStatusMessage(msg, "info")

    def updateWidgets(self):
        em = self.context.__parent__
        for fielddata in em.registrationFields:
            if fielddata['fieldtype'] == 'List':
                self.fields[fielddata['name']].widgetFactory = \
                                                    CheckBoxFieldWidget
                self.fields[fielddata['name']].field.context = self.context

        super(dexterity.AddForm, self).updateWidgets()
        if self.userRegistering:
            self.widgets['new_user'].value = u'yes'
        self.widgets['noshow'].mode = 'hidden'

    def updateFields(self):
        super(dexterity.AddForm, self).updateFields()
        em = self.context.__parent__
        addDynamicFields(self, em.registrationFields)
