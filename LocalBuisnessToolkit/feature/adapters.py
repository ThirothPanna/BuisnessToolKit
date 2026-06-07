from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import Group


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit)
        business_owner_group, _ = Group.objects.get_or_create(name="BusinessOwner")
        user.groups.add(business_owner_group)
        return user
