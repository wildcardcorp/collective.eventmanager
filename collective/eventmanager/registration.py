from five import grok
from zope import schema
from plone.directives import form, dexterity
from plone.z3cform.fieldsets import utils
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from Products.CMFCore.utils import getToolByName

from collective.eventmanager.event import sendEMail
from collective.eventmanager.interfaces import ILayer
from collective.eventmanager import EventManagerMessageFactory as _


class IRegistration(form.Schema):
    """A registration for an event"""

    title = schema.TextLine(
            title=_(u"Name"),
        )

    description = schema.TextLine(
            title=_(u"EMail Address"),
        )


def getNumApprovedAndConfirmed(context):
    catalog = getToolByName(context, 'portal_catalog')
    searchDict = {
        'query': ('/'.join(context.getPhysicalPath())),
        'depth': 1,
        'portal_type': 'collective.eventmanager.Registration',
        'review_state': 'approved'}
    brains = [a for a in catalog.searchResults(searchDict)]
    searchDict['review_state'] = 'confirmed'
    brains.append([a for a in catalog.searchResults(searchDict)])

    return len(brains)


@grok.subscribe(IRegistration, IObjectAddedEvent)
def handleNewRegistration(reg, event):
    parentevent = reg.__parent__.__parent__
    regfolderish = reg.__parent__
    hasWaitingList = parentevent.enableWaitingList
    hasPrivateReg = parentevent.privateRegistration
    #isPrivateEvent = parentevent.privateEvent
    maxreg = parentevent.maxRegistrations
    numRegApproved = getNumApprovedAndConfirmed(regfolderish)

    workflowTool = getToolByName(reg, "portal_workflow")

    # private registration means manual adding of registrations
    if hasPrivateReg:
        workflowTool.doActionFor(parentevent, 'approve')

    # haven't hit max, 'approve'
    elif maxreg == None or numRegApproved <= maxreg:
        workflowTool.doActionFor(reg, 'approve')
        sendEMail(parentevent, 'thank you', [reg.description], reg)

    # waiting list, and hit max == remain 'submitted' (on waiting list)
    elif hasWaitingList:
        sendEMail(parentevent, 'on waiting list', [reg.description], reg)

    # all other cases, 'deny'
    else:
        workflowTool.doActionFor(reg, 'deny')
        sendEMail(parentevent, 'registration full', [reg.description], reg)


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in registration_templates/view.pt
    """

    grok.context(IRegistration)
    grok.require('zope2.View')
    grok.name('view')
    grok.layer(ILayer)

    def dynamicFields(self):
        registrationFields = \
            self.context.__parent__.__parent__.registrationFields
        fields = []
        for fielddata in registrationFields:
            n = fielddata['name']
            t = fielddata['fieldtype']
            v = getattr(self.context, fielddata['name'])

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

    def updateFields(self):
        super(dexterity.EditForm, self).updateFields()
        em = self.context.__parent__.__parent__
        addDynamicFields(self, em.registrationFields)


class AddForm(dexterity.AddForm):
    grok.name('collective.eventmanager.Registration')

    def updateFields(self):
        super(dexterity.AddForm, self).updateFields()
        em = self.context.__parent__
        addDynamicFields(self, em.registrationFields)
