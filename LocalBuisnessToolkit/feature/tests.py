from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Customer, Invoice


class InvoiceViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner",
            email="owner@example.com",
            password="password123",
        )
        self.customer = Customer.objects.create(
            owner=self.user,
            name="Acme Co",
            email="billing@acme.test",
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            user=self.user,
            amount=Decimal("25.00"),
            status="unpaid",
            description="Initial work",
            due_date=date(2026, 6, 21),
        )
        self.client.force_login(self.user)

    def test_invoice_detail_renders_invoice(self):
        response = self.client.get(
            reverse("feature:invoice_detail", args=[self.invoice.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invoice #")
        self.assertContains(response, "Acme Co")
        self.assertContains(response, "Initial work")

    def test_invoice_edit_updates_invoice(self):
        response = self.client.post(
            reverse("feature:invoice_edit", args=[self.invoice.id]),
            {
                "customer": self.customer.id,
                "amount": "40.50",
                "status": "paid",
                "description": "Updated work",
                "due_date": "2026-07-01",
            },
        )

        self.assertRedirects(
            response,
            reverse("feature:invoice_detail", args=[self.invoice.id]),
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount, Decimal("40.50"))
        self.assertEqual(self.invoice.status, "paid")
        self.assertEqual(self.invoice.description, "Updated work")
        self.assertEqual(self.invoice.due_date, date(2026, 7, 1))
