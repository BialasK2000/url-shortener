from shortener.utils import SHORT_CODE_CHARS, SHORT_CODE_LENGTH, generate_short_code


def test_generate_short_code() -> None:
    code = generate_short_code()

    assert len(code) == SHORT_CODE_LENGTH
    assert all(char in SHORT_CODE_CHARS for char in code)


def test_generated_codes_are_unique() -> None:
    codes = {generate_short_code() for _ in range(1000)}

    assert len(codes) == 1000
