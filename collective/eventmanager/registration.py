from five import grok
from zope import schema
from plone.directives import form, dexterity
from plone.z3cform.fieldsets import utils

from collective.eventmanager import EventManagerMessageFactory as _


class IRegistration(form.Schema):
    """A registration for an event"""

    title = schema.TextLine(
            title=_(u"Name"),
        )

    description = schema.TextLine(
            title=_(u"EMail Address"),
        )


class EditForm(dexterity.EditForm):
    grok.context(IRegistration)

    def updateFields(self):
        super(dexterity.EditForm, self).updateFields()

        em = self.context.__parent__.__parent__
        fields = em.registrationFields
        for fielddata in fields:
            field = getattr(schema,
                            fielddata['fieldtype'])(
                                title=unicode(fielddata['name']),
                                required=fielddata['required'])
            field.__name__ = str(fielddata['name'])
            field.interface = IRegistration
            utils.add(self, field)


class AddForm(dexterity.AddForm):
    grok.name('collective.eventmanager.Registration')

    def updateFields(self):
        super(dexterity.AddForm, self).updateFields()
        em = self.context.__parent__
        fields = em.registrationFields
        for fielddata in fields:
            field = getattr(schema,
                            fielddata['fieldtype'])(
                                title=unicode(fielddata['name']),
                                required=fielddata['required'])
            field.__name__ = str(fielddata['name'])
            field.interface = IRegistration
            utils.add(self, field)


class View(grok.View):
    """Default view (called "@@view"") for an event.

    The associated template is found in registration_templates/view.pt
    """

    grok.context(IRegistration)
    grok.require('zope2.View')
    grok.name('view')

    def __call__(self):
        import pdb;pdb.set_trace()

    def update(self):
        import pdb;pdb.set_trace()
