from zope.interface import implements
from zope.component import getUtility
from persistent.mapping import PersistentMapping
from zope.component import getMultiAdapter
from zope.annotation.interfaces import IAnnotations

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.formlib import form

from Products.PloneGetPaid.browser.cart import ShoppingCartAddItem
from getpaid.core.interfaces import ILineItemFactory, IShoppingCartUtility
from getpaid.core.interfaces import IFormSchemas
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.browser.checkout import \
    CheckoutAddress as BaseCheckoutAddress, \
    CheckoutReviewAndPay as BaseCheckoutReviewAndPay, \
    CheckoutWizard, CheckoutController, OrderFormatter

from collective.eventmanager.utils import findRegistrationObject
from collective.eventmanager.interfaces import IEMWizard
from getpaid.core.order import Order
from cPickle import loads, dumps
from AccessControl import getSecurityManager
from Products.CMFPlone.i18nl10n import utranslate
from zope.formlib.interfaces import WidgetInputError

_getpaid_key = 'getpaid.configuration'


def getCart(context):
    cart = getUtility(IShoppingCartUtility).get(context, key='oneshot:_')
    factory = getMultiAdapter((cart, context), ILineItemFactory)
    if len(factory.cart) == 0:
        factory.create(quantity=1)
    return cart


def fixedCreateTransientOrder(self):
    order = Order()
    cart = getCart(self.context)
    formSchemas = getUtility(IFormSchemas)

    # shopping cart is attached to the session, but we want to switch the
    # storage to the persistent zodb, we pickle to get a clean copy to store.
    adapters = self.wizard.data_manager.adapters

    order.shopping_cart = loads(dumps(cart))

    for section in ('contact_information', 'billing_address',
                    'shipping_address'):
        interface = formSchemas.getInterface(section)
        bag = formSchemas.getBagClass(section).frominstance(
            adapters[interface])
        setattr(order, section, bag)

    order.order_id = self.wizard.data_manager.get('order_id')
    order.user_id = getSecurityManager().getUser().getId()

    return order


class PayForEventView(ShoppingCartAddItem):

    def __call__(self):
        # first, make sure getpaid configuration for price is set.
        if not self.context.registrationFee:
            return self.request.response.redirect(
                self.context.absolute_url())
        annotations = IAnnotations(self.context)
        if _getpaid_key not in annotations:
            annotations[_getpaid_key] = PersistentMapping()
        settings = annotations[_getpaid_key]
        if 'price' not in settings or \
                settings['price'] != self.context.registrationFee:
            settings['price'] = self.context.registrationFee
        url = self.context.absolute_url() + '/@@getpaid-checkout-wizard'
        return self.request.response.redirect(url)


class CheckoutAddress(BaseCheckoutAddress):
    createTransientOrder = fixedCreateTransientOrder

    fields_to_hide = (
        'form.marketing_preference',
        'form.email_html_format'
        )

    def getWidgetsBySectionName(self, section_name):
        widgets = super(CheckoutAddress, self).getWidgetsBySectionName(
            section_name)
        for widget in [w for w in widgets]:
            if widget.name in self.fields_to_hide:
                widgets.remove(widget)
            elif widget.name == 'form.email':
                widget.hint = u'Must match email you used to sign up with.'
        return widgets

    def validate(self, action, data):
        errors = super(CheckoutAddress, self).validate(action, data)
        reg = findRegistrationObject(self.context, data.get('email'))
        if reg is None:
            widget = self.widgets.get('email')
            error = WidgetInputError(field_name='email',
                widget_title=_(u'Email'),
                errors=_(u'Not registered email.'))
            widget._error = error
            errors += (error,)
        elif reg.paid_fee:
            widget = self.widgets.get('email')
            error = WidgetInputError(field_name='email',
                widget_title=_(u'Email'),
                errors=_(u'This attendee has already paid.'))
            widget._error = error
            errors += (error,)
        return errors


class CheckoutReviewAndPay(BaseCheckoutReviewAndPay):
    template = ZopeTwoPageTemplateFile('templates/checkout-review-pay.pt')
    createTransientOrder = fixedCreateTransientOrder

    def renderCart(self):
        cart = getCart(self.context)
        if not cart:
            return _(u"N/A")

        for column in self.columns:
            if hasattr(column, 'title'):
                column.title = utranslate(domain='plonegetpaid',
                                          msgid=column.title,
                                          context=self.request)

        # create an order so that tax/shipping utilities have full order
        # information to determine costs (ie. billing/shipping address ).
        order = self.createTransientOrder()
        formatter = OrderFormatter(order, self.request, cart.values(),
            prefix=self.prefix,
            visible_column_names=[c.name for c in self.columns],
            columns=self.columns)

        formatter.cssClasses['table'] = 'listing'
        return formatter()

    @form.action(_(u"Make Payment"), name="make-payment")
    def makePayment(self, action, data):
        reg = findRegistrationObject(self.context,
            self.wizard.data_manager.get('form.email'))
        if reg is None:
            raise Exception('oops, there was an error.')
        super(CheckoutReviewAndPay, self).makePayment.success_handler(
            self, action, data)
        reg.paid_fee = True


class EMCheckoutWizard(CheckoutWizard):
    implements(IEMWizard)

    def checkShoppingCart(self):
        return True


class EMCheckoutController(CheckoutController):
    def checkShippableCart(self):
        return False
