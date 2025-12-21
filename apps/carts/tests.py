from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from apps.users.models import User
from apps.carts.models import Cart, CartItem
from apps.stock_management.models import Inventory
from apps.sales.models import SalesOrder


class CartCheckoutSelectedItemsTest(APITestCase):
	def setUp(self):
		# Create customer user
		self.user = User.objects.create_user(
			username='customer1', password='pass1234', role=User.Role.CUSTOMER
		)
		self.client.force_authenticate(self.user)

		# Create inventory items
		self.inv1 = Inventory.objects.create(
			item_name='Brake Pad', category='local', vehicle_type='two_wheeler',
			quantity=Decimal('10.00'), retail_pricing=Decimal('100.00'), mrp=Decimal('120.00')
		)
		self.inv2 = Inventory.objects.create(
			item_name='Clutch Plate', category='local', vehicle_type='two_wheeler',
			quantity=Decimal('5.00'), retail_pricing=Decimal('200.00'), mrp=Decimal('240.00')
		)

		# Create cart and items
		self.cart = Cart.objects.create(user=self.user, is_active=True)
		self.item1 = CartItem.objects.create(cart=self.cart, inventory=self.inv1, quantity=Decimal('2.00'), price=self.inv1.retail_pricing)
		self.item2 = CartItem.objects.create(cart=self.cart, inventory=self.inv2, quantity=Decimal('1.00'), price=self.inv2.retail_pricing)

	def test_checkout_selected_items_and_delivery_deducts_inventory(self):
		checkout_url = '/api/carts/cart/checkout/'
		body = {
			'payment_method': 'cash',
			'delivery_address': '221B Baker Street',
			'delivery_city': 'London',
			'selected_item_ids': [self.item1.id],
		}

		# Checkout only item1
		resp = self.client.post(checkout_url, data=body, format='json')
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
		order_id = resp.data['order']['id']

		# Ensure only selected item removed from cart
		remaining_items = list(self.cart.items.values_list('id', flat=True))
		self.assertIn(self.item2.id, remaining_items)
		self.assertNotIn(self.item1.id, remaining_items)

		# Verify order has 1 item with correct quantity
		order = SalesOrder.objects.get(id=order_id)
		self.assertEqual(order.items.count(), 1)
		order_item = order.items.first()
		self.assertEqual(order_item.inventory_id, self.inv1.id)
		self.assertEqual(order_item.quantity, Decimal('2.00'))

		# Inventory should NOT be deducted yet
		self.inv1.refresh_from_db()
		self.assertEqual(self.inv1.quantity, Decimal('10.00'))

		# Now mark order as delivered to deduct inventory via model method
		order.update_order_status('delivered')

		# Inventory should be deducted for item1 only
		self.inv1.refresh_from_db()
		self.inv2.refresh_from_db()
		self.assertEqual(self.inv1.quantity, Decimal('8.00'))  # 10 - 2
		self.assertEqual(self.inv2.quantity, Decimal('5.00'))  # unchanged
