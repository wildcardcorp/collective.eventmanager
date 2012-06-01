from persistent.mapping import PersistentMapping
from zope.component import getMultiAdapter
from zope.annotation.interfaces import IAnnotations

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.formlib import form

from Products.PloneGetPaid.browser.cart import ShoppingCartAddItem
from getpaid.core.interfaces import ILineItemFactory
from Products.PloneGetPaid.i18n import _
from Products.PloneGetPaid.browser.checkout import \
    CheckoutAddress as BaseCheckoutAddress, \
    CheckoutReviewAndPay as BaseCheckoutReviewAndPay

from collective.eventmanager.utils import findRegistrationObject

_getpaid_key = 'getpaid.configuration'


class PayForEventView(ShoppingCartAddItem):

    def __call__(self):
        # first, make sure getpaid configuration for price is set.
        annotations = IAnnotations(self.context)
        if _getpaid_key not in annotations:
            annotations[_getpaid_key] = PersistentMapping()
        settings = annotations[_getpaid_key]
        if 'price' not in settings or \
                settings['price'] != self.context.registrationFee:
            settings['price'] = self.context.registrationFee
        # create a line item and add it to the cart
        item_factory = getMultiAdapter((self.cart, self.context),
            ILineItemFactory)

        item_factory.create(quantity=1)
        url = self.context.absolute_url() + '/@@getpaid-checkout-wizard'
        return self.request.response.redirect(url)


class CheckoutAddress(BaseCheckoutAddress):

    fields_to_hide = (
        'form.marketing_preference',
        'form.email_html_format'
        )

    def getWidgetsBySectionName(self, section_name):
        widgets = super(CheckoutAddress, self).getWidgetsBySectionName(
            section_name)
        reg = findRegistrationObject(self.context)
        for widget in [w for w in widgets]:
            if widget.name in self.fields_to_hide:
                widgets.remove(widget)
            elif widget.name in ('form.name', 'form.bill_name',
                                 'form.ship_name'):
                widget._missing = reg.title
            elif widget.name == 'form.email':
                widget._missing = reg.email
        return widgets


class CheckoutReviewAndPay(BaseCheckoutReviewAndPay):
    template = ZopeTwoPageTemplateFile('templates/checkout-review-pay.pt')

    def getWidgetsBySectionName(self, section_name):
        widgets = super(CheckoutReviewAndPay, self).getWidgetsBySectionName(
            section_name)
        reg = findRegistrationObject(self.context)
        for widget in [w for w in widgets]:
            if widget.name == 'form.name_on_card':
                widget._missing = reg.email
        return widgets

    @form.action(_(u"Make Payment"), name="make-payment")
    def makePayment(self, action, data):
        super(CheckoutReviewAndPay, self).makePayment.success_handler(
            self, action, data)
        reg = findRegistrationObject(self.context)
        reg.paid_fee = True
