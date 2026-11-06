from sovereign_closet.domain.style_brief import StyleBrief

def test_style_brief_defaults():
    brief = StyleBrief(query="dark founder streetwear")
    assert "top" in brief.required_slots
    assert "black" in brief.palette
