from decimal import Decimal
from django.test import TestCase

from apps.users.models import User
from apps.sales.models import SalesOrder


class PaymentStatusSyncTests(TestCase):
	def setUp(self):
		# Minimal customer user
		self.customer = User.objects.create_user(
			username='sync_customer',
			email='sync@example.com',
			password='pass1234',
			role=User.Role.CUSTOMER,
		)

	def _create_order(self, total_amount=Decimal('100.00')):
		order = SalesOrder.objects.create(
			customer=self.customer,
			delivery_address='123 Test Street',
			delivery_city='Test City',
			total_amount=total_amount,
		)
		return order

	def test_invoice_to_sales_order_payment_sync(self):
		"""Changing invoice payment status updates sales order status and amounts."""
		order = self._create_order(total_amount=Decimal('100.00'))

		# Generate invoice from order
		invoice = order.generate_invoice()

		# Sanity: initial mapping should be pending
		self.assertEqual(invoice.payment_status, 'pending')
		self.assertEqual(invoice.paid_amount, Decimal('0.00'))
		self.assertIsNone(invoice.payment_method)

		# Update invoice to paid and verify sales order sync
		invoice.update_payment_status('paid')

		order.refresh_from_db()
		invoice.refresh_from_db()

		self.assertEqual(invoice.payment_status, 'paid')
		self.assertEqual(order.payment_status, 'paid')

		# Update invoice to pending and verify sales order sync back
		invoice.update_payment_status('pending')
		order.refresh_from_db()
		self.assertEqual(order.payment_status, 'pending')

	def test_invoice_paid_amount_change_syncs_sales_order(self):
		"""Changing invoice paid amount (via serializer-like flow) syncs sales order."""
		order = self._create_order(total_amount=Decimal('100.00'))
		invoice = order.generate_invoice()

		# Simulate partial payment via Payment record
		Payment.from_invoice(invoice=invoice, amount=Decimal('50.00'), payment_method='upi')

		order.refresh_from_db()
		self.assertEqual(order.paid_amount, Decimal('50.00'))
		self.assertEqual(order.payment_method, 'upi')
		self.assertEqual(order.payment_status, 'pending')

	def test_sales_order_to_invoice_payment_sync(self):
		"""Changing sales order payment status updates invoice payment status."""
		order = self._create_order(total_amount=Decimal('100.00'))
		invoice = order.generate_invoice()

		# Change order to credit_sale and verify invoice reflects the mapping
		order.update_payment_status('credit_sale')

		order.refresh_from_db()
		invoice.refresh_from_db()

		self.assertEqual(order.payment_status, 'credit_sale')
		self.assertEqual(invoice.payment_status, 'credit_sale')


class PaymentModelSyncTests(TestCase):
	def setUp(self):
		self.customer = User.objects.create_user(
			username='payment_customer',
			email='payment@example.com',
			password='pass1234',
			role=User.Role.CUSTOMER,
		)

	def _create_order_with_invoice(self, total_amount=Decimal('100.00')):
		order = SalesOrder.objects.create(
			customer=self.customer,
			total_amount=total_amount,
			delivery_address='123 Payment Street',
			delivery_city='Payville',
		)
		invoice = order.generate_invoice()
		invoice.total_amount = total_amount
		invoice.save(update_fields=['total_amount'])
		return order, invoice

	def test_payment_updates_invoice_and_order_totals(self):
		order, invoice = self._create_order_with_invoice(total_amount=Decimal('100.00'))

		Payment.objects.create(
			invoice=invoice,
			paid_amount=Decimal('50.00'),
			payment_method='cash',
			payment_status='pending',
		)

		order.refresh_from_db()
		invoice.refresh_from_db()

		self.assertEqual(order.paid_amount, Decimal('50.00'))
		self.assertEqual(order.payment_status, 'pending')
		self.assertEqual(invoice.paid_amount, Decimal('50.00'))
		self.assertEqual(invoice.payment_status, 'pending')
		self.assertEqual(invoice.payment_method, 'cash')

	def test_multiple_payments_mark_as_paid_when_total_covered(self):
		order, invoice = self._create_order_with_invoice(total_amount=Decimal('100.00'))

		Payment.objects.create(
			invoice=invoice,
			paid_amount=Decimal('60.00'),
			payment_method='cash',
		)

		Payment.objects.create(
			invoice=invoice,
			paid_amount=Decimal('40.00'),
			payment_method='card',
			payment_status='paid',
		)

		order.refresh_from_db()
		invoice.refresh_from_db()

		self.assertEqual(order.paid_amount, Decimal('100.00'))
		self.assertEqual(order.payment_status, 'paid')
		self.assertEqual(order.payment_method, 'card')
		self.assertEqual(invoice.paid_amount, Decimal('100.00'))
		self.assertEqual(invoice.payment_status, 'paid')
		self.assertEqual(invoice.payment_method, 'card')

