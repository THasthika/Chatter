from user import User
from unittest.mock import MagicMock
from utils import Gender, Preference


def test_user_match():
    websocket = MagicMock()
    user_a = User(websocket)
    user_a.register(1, Gender.MALE, Preference(
        gender=Gender.FEMALE
    ))
    user_b = User(websocket)
    user_b.register(1, Gender.MALE, Preference())

    assert user_a.is_free == True
    assert user_b.is_free == True

    assert user_a.check_match(user_b) == False
