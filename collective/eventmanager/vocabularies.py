from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm


RegistrationRowAvailableFieldTypes = SimpleVocabulary(
    [SimpleTerm(value=u'TextLine', title=u'Text Line'),
     SimpleTerm(value=u'Text', title=u'Text Area'),
     SimpleTerm(value=u'Float', title=u'Number'),
     SimpleTerm(value=u'Bool', title=u'Check Box'),
     SimpleTerm(value=u'Datetime', title=u'Date/Time'),
     SimpleTerm(value=u'URI', title=u'URL'),
     SimpleTerm(value=u'List', title=u'Check list')]
    )
