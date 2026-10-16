from django.test import Client, TestCase

from .tests.factories import UserFactory


class ClientTestCase(TestCase):
    def setUp(self):
        """Create the attributes:

        * anonymous_client: client not logged in
        * auth_client: client authenticated, but without permissions
        * auth_user: user object behind auth_client
        * admin_user: superuser
        """
        super().setUp()

        self.anonymous_client = Client()
        self.auth_client, self.auth_user = self.create_client()
        self.admin_client, self.admin_user = self.create_client(superuser=True)
        session = self.admin_client.session
        session["admin_mfa"] = {
            "user_id": str(self.admin_user.pk),
            "acr": "eidas1-mfa",
        }

        session.save()

    def create_user(self, superuser=False):
        return UserFactory(superuser=superuser)

    def create_client(self, superuser=False):
        user = self.create_user(superuser=superuser)
        client = Client()
        client.force_login(user=user)
        return (client, user)
