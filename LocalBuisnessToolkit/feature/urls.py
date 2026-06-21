from django.urls import path
from . import views

app_name = 'feature'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('appointments/', views.appointment, name='appointments'),
    path('appointments/create/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/edit/', views.appointment_edit, name='appointment_edit'),
    path('appointments/<int:appointment_id>/delete/', views.appointment_delete, name='appointment_delete'),

    # Customers (appointment-like feature)
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/add/', views.customer_create, name='add_customer'),  # backward-compatible alias
    path('customers/', views.customers, name='customers'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),

    path('invoices/', views.invoices, name='invoices'),
    path('invoices/add/', views.add_invoice, name='add_invoice'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:invoice_id>/delete/', views.invoice_delete, name='invoice_delete'),

    path('notifications/', views.notification_center, name='notifications'),

    path('notifications/api/', views.get_notifications_api, name='notifications_api'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('settings/', views.settings, name='settings'),
]

