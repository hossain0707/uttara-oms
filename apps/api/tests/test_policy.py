from uuid import uuid4
from unittest.mock import MagicMock
from app.auth import Actor
from app.policies import can_approve, is_thana_admin, CATEGORIES
from app.security import normalize_phone
import pytest


def actor(role, scope=None):
    return Actor(uuid4(), "example.invalid", [(role, scope)], True)


def test_four_distinct_categories():
    assert CATEGORIES == {"RUKON", "WORKER", "ASSOCIATE", "SUPPORTER"}


def test_thana_admin_can_approve():
    admin = actor("THANA_ADMIN")
    assert is_thana_admin(admin)
    assert can_approve(MagicMock(), admin, uuid4(), uuid4())


def test_viewer_cannot_approve():
    assert not can_approve(MagicMock(), actor("THANA_VIEWER"), uuid4())


def test_phone_canonicalization():
    assert normalize_phone("+8801712345678") == "01712345678"
    assert normalize_phone("8801712345678") == "01712345678"


def test_invalid_phone_rejected():
    with pytest.raises(ValueError):
        normalize_phone("12345")
