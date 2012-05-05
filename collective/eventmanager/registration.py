from five import grok
from zope import schema
from plone.directives import form, dexterity
from plone.z3cform.fieldsets import utils
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from Products.CMFCore.utils import getToolByName
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


def sendEMail(reg, emailtype):
    pass


@grok.subscribe(IRegistration, IObjectAddedEvent)
def handleNewRegistration(reg, event):
    parentevent = reg.__parent__.__parent__
    regfolderish = reg.__parent__
    hasWaitingList = parentevent.enableWaitingList
    hasPrivateReg = parentevent.privateRegistration
    isPrivateEvent = parentevent.privateEvent
    maxreg = parentevent.maxRegistrations
    numRegApproved = getNumApprovedAndConfirmed(regfolderish)

    workflowTool = getToolByName(reg, "portal_workflow")

    # private registration through a private event or explicitely defined
    # indicates immediate approval
    if isPrivateEvent or hasPrivateReg:
        workflowTool.doActionFor(reg, 'approve')

    # if there's room left for the registration, approve it
    elif maxreg == None or numRegApproved < maxreg:
        workflowTool.doActionFor(reg, 'approve')
        sendEMail(reg, 'registration successful')

    # no space left, but there is a waiting list, send email indicating so
    elif hasWaitingList and (maxreg != None and numRegApproved >= maxreg):
        sendEMail(reg, 'on waiting list')

    # no space left, and no waiting list, send registration full email
    elif not hasWaitingList and (maxreg != None and numRegApproved >= maxreg):
        workflowTool.doActionFor(reg, 'deny')
        sendEMail(reg, 'registration full')


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
