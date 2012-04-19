from Products.ATContentTypes.interface import IATEvent
from archetypes.schemaextender.interfaces \
    import ISchemaExtender, \
            ISchemaModifier, \
            IBrowserLayerAwareExtender
from zope.component import adapts
from zope.interface import implements

from interfaces import IEventManagerLayer


class EventExtender(object):
    adapts(IATEvent)
    implements(ISchemaExtender, ISchemaModifier, IBrowserLayerAwareExtender)

    layer = IEventManagerLayer

    fields = [

    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields

    def fiddle(self, schema):
        # hide attendees
        new_field = schema['attendees'].copy()
        new_field.widget.visible = {'edit': 'invisible', 'view': 'invisible'}
        schema['attendees'] = new_field
