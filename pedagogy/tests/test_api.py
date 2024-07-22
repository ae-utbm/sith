import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from model_bakery.recipe import Recipe

from core.baker_recipes import subscriber_user
from core.models import RealGroup, User
from pedagogy.models import UV


class UVSearchTest(TestCase):
    """Test UV guide rights for view and API."""

    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.get(username="root")
        cls.url = reverse("api:fetch_uvs")
        uv_recipe = Recipe(UV, author=cls.root)
        uvs = [
            uv_recipe.prepare(
                code="AP4A", credit_type="CS", semester="AUTUMN", department="GI"
            ),
            uv_recipe.prepare(
                code="MT01", credit_type="CS", semester="AUTUMN", department="TC"
            ),
            uv_recipe.prepare(
                code="PHYS11", credit_type="CS", semester="AUTUMN", department="TC"
            ),
            uv_recipe.prepare(
                code="TNEV", credit_type="TM", semester="SPRING", department="TC"
            ),
            uv_recipe.prepare(
                code="MT10", credit_type="TM", semester="AUTUMN", department="IMSI"
            ),
            uv_recipe.prepare(
                code="DA50",
                credit_type="TM",
                semester="AUTUMN_AND_SPRING",
                department="GI",
            ),
        ]
        UV.objects.bulk_create(uvs)

    def test_permissions(self):
        # Test with anonymous user
        response = self.client.get(self.url)
        assert response.status_code == 403

        # Test with not subscribed user
        self.client.force_login(baker.make(User))
        response = self.client.get(self.url)
        assert response.status_code == 403

        for user in (
            self.root,
            subscriber_user.make(),
            baker.make(
                User,
                groups=[
                    RealGroup.objects.get(pk=settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)
                ],
            ),
        ):
            # users that have right
            with self.subTest():
                self.client.force_login(user)
                response = self.client.get(self.url)
                assert response.status_code == 200

    def test_format(self):
        """Test that the return data format is correct"""
        self.client.force_login(self.root)
        res = self.client.get(self.url + "?search=PA00")
        uv = UV.objects.get(code="PA00")
        assert res.status_code == 200
        assert json.loads(res.content) == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": uv.id,
                    "title": uv.title,
                    "code": uv.code,
                    "credit_type": uv.credit_type,
                    "semester": uv.semester,
                    "department": uv.department,
                }
            ],
        }

    def test_search_by_code(self):
        self.client.force_login(self.root)
        res = self.client.get(self.url + "?search=MT")
        assert res.status_code == 200
        assert {uv["code"] for uv in json.loads(res.content)["results"]} == {
            "MT01",
            "MT10",
        }

    def test_search_by_credit_type(self):
        self.client.force_login(self.root)
        res = self.client.get(self.url + "?credit_type=CS")
        assert res.status_code == 200
        codes = [uv["code"] for uv in json.loads(res.content)["results"]]
        assert codes == ["AP4A", "MT01", "PHYS11"]
        res = self.client.get(self.url + "?credit_type=CS&credit_type=OM")
        assert res.status_code == 200
        codes = {uv["code"] for uv in json.loads(res.content)["results"]}
        assert codes == {"AP4A", "MT01", "PHYS11", "PA00"}

    def test_search_by_semester(self):
        self.client.force_login(self.root)
        res = self.client.get(self.url + "?semester=SPRING")
        assert res.status_code == 200
        codes = {uv["code"] for uv in json.loads(res.content)["results"]}
        assert codes == {"DA50", "TNEV", "PA00"}

    def test_search_multiple_filters(self):
        self.client.force_login(self.root)
        res = self.client.get(
            self.url + "?semester=AUTUMN&credit_type=CS&department=TC"
        )
        assert res.status_code == 200
        codes = {uv["code"] for uv in json.loads(res.content)["results"]}
        assert codes == {"MT01", "PHYS11"}

    def test_search_fails(self):
        self.client.force_login(self.root)
        res = self.client.get(self.url + "?credit_type=CS&search=DA")
        assert res.status_code == 200
        assert json.loads(res.content)["results"] == []

    def test_search_pa00_fail(self):
        self.client.force_login(self.root)
        # Search with UV code
        response = self.client.get(reverse("pedagogy:guide"), {"search": "IFC"})
        self.assertNotContains(response, text="PA00")

        # Search with first letter of UV code
        response = self.client.get(reverse("pedagogy:guide"), {"search": "I"})
        self.assertNotContains(response, text="PA00")

        # Search with UV manager
        response = self.client.get(reverse("pedagogy:guide"), {"search": "GILLES"})
        self.assertNotContains(response, text="PA00")

        # Search with department
        response = self.client.get(reverse("pedagogy:guide"), {"department": "TC"})
        self.assertNotContains(response, text="PA00")

        # Search with semester
        response = self.client.get(reverse("pedagogy:guide"), {"semester": "CLOSED"})
        self.assertNotContains(response, text="PA00")

        # Search with language
        response = self.client.get(reverse("pedagogy:guide"), {"language": "EN"})
        self.assertNotContains(response, text="PA00")

        # Search with credit type
        response = self.client.get(reverse("pedagogy:guide"), {"credit_type": "TM"})
        self.assertNotContains(response, text="PA00")
