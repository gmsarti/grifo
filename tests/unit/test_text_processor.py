from app.utils.text_processor import get_text_splitter


def test_text_splitter_configuration():
    splitter = get_text_splitter()
    assert splitter._chunk_size == 1000
    assert splitter._chunk_overlap == 200
    assert "\n\n" in splitter._separators


def test_text_splitting():
    splitter = get_text_splitter()
    text = "Esta é uma frase de teste. " * 100
    chunks = splitter.split_text(text)

    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk) <= 1000


if __name__ == "__main__":
    print("Running tests...")
    test_text_splitter_configuration()
    print("test_text_splitter_configuration: OK")
    test_text_splitting()
    print("test_text_splitting: OK")
    print("All tests passed!")
