import pytest
from pydantic import ValidationError
from sovereign_closet.canon.identity import IdentityCanon, CANON

def test_default_canon_is_locked():
    assert CANON.immutable_identity is True
    assert CANON.standalone_image_only is True
    assert CANON.gauge_terminal_inches == 5.0
    assert CANON.protected_back_text == "RARE ONE"

def test_rare_one_text_is_protected():
    with pytest.raises(ValidationError):
        IdentityCanon(protected_back_text="RARE 1")
