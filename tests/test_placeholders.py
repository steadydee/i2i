from backend.templates import extract_placeholders

def test_extract_plaintext():
    sample = b"Hello {{client}}, amount is {{amount}}. {{client}} again."
    names = extract_placeholders(sample, ".txt")
    assert names == ["amount","client"]
