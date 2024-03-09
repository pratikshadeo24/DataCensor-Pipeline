import pytest
from unittest.mock import mock_open
from assignment1 import main


@pytest.fixture
def mock_recognize_entity(mocker):
    # Mock the recognize_entity function
    mock = mocker.patch('assignment1.main.recognize_entity')

    # Create a mock spaCy Doc with entities
    MockEntity = type('MockEntity', (), {})
    entity1 = MockEntity()
    entity1.text = 'John Doe'
    entity1.label_ = 'PERSON'
    entity1.start_char = 0
    entity1.end_char = 8

    entity2 = MockEntity()
    entity2.text = '123456789'
    entity2.label_ = 'PHONE'
    entity2.start_char = 27
    entity2.end_char = 36

    mock_doc = type('MockDoc', (), {'ents': [entity1, entity2]})

    mock.return_value = mock_doc()
    return mock


@pytest.fixture
def mock_nlp_hugging_face(mocker):
    # Mock the Hugging Face model's output
    return [
        {'entity': 'I-PER', 'start': 18},
        {'entity': 'B-PER', 'start': 23},
        {'entity': 'I-LOC', 'start': 38},
        {'entity': 'B-LOC', 'start': 42}
    ]


@pytest.fixture
def mock_another_recognize_entity(mocker):
    # Mock the recognize_entity function for Spacy
    mocked_nlp_spacy = mocker.Mock()
    mocked_doc = mocker.Mock()
    mocked_nlp_spacy.return_value = mocked_doc
    mocked_doc.ents = [mocker.Mock(text='John Doe', label_='PERSON')]
    return mocked_nlp_spacy


def test_recognize_entity_spacy(mocker):
    # Mock a spaCy-like model's behavior
    mocked_nlp = mocker.Mock()
    mocked_doc = mocker.Mock()
    mocked_nlp.return_value = mocked_doc
    mocked_doc.ents = ['PERSON', 'DATE']

    text = "Sample text for testing"
    result = main.recognize_entity(mocked_nlp, text)

    # Assert nlp_model was called with the text
    mocked_nlp.assert_called_once_with(text)
    # Assert the result is as expected
    assert result == mocked_doc


def test_recognize_entity_huggingface(mocker):
    # Mock a Hugging Face-like model's behavior
    mocked_nlp = mocker.Mock()
    mocked_output = {'entities': ['PER', 'LOC']}
    mocked_nlp.return_value = mocked_output

    text = "Sample text for testing"
    result = main.recognize_entity(mocked_nlp, text)

    # Assert nlp_model was called with the text
    mocked_nlp.assert_called_once_with(text)
    # Assert the result is as expected
    assert result == mocked_output


@pytest.mark.parametrize("text, start, end, word, expected", [
    ("Hello James", 6, 11, "James", "Hello █████"),
    ("Please contact me at 1234-5678", 21, 30, "1234-5678", "Please contact me at █████████"),
    ("Allen is at the start", 0, 5, "Allen", "█████ is at the start"),
    ("See you later in the office, Bob", 29, 32, "Bob", "See you later in the office, ███"),
])
def test_replace_with_black_block_by_indices(text, start, end, word, expected):
    censored_text = main.replace_with_black_block_by_indices(text, start, end, word)
    assert censored_text == expected


def test_censor_spacy_censors_correct_entities(mock_recognize_entity):
    text = "John Doe's phone number is 123456789."
    entities_to_censor = ['PERSON', 'PHONE']

    censored_text = main.censor_spacy(text, entities_to_censor, {'PERSON': {'count': 0, 'indices': []}})
    assert censored_text == "████████'s phone number is █████████."


def test_censor_spacy_ignores_uncensored_entities(mock_recognize_entity):
    text = "John Doe lives in New York."
    entities_to_censor = ['PHONE']  # Not censoring 'PERSON' or 'GPE'

    censored_text = main.censor_spacy(text, entities_to_censor, {})
    assert censored_text == "John Doe lives in New York."


def test_censor_spacy_no_entities_to_censor(mock_recognize_entity):
    text = "Just a plain sentence with no entities."
    entities_to_censor = []

    censored_text = main.censor_spacy(text, entities_to_censor, {'PERSON': 0})
    assert censored_text == text


def test_censor_hf_entities(mocker, mock_nlp_hugging_face):
    mocker.patch('assignment1.main.recognize_entity', return_value=mock_nlp_hugging_face)
    text = "Hello, my name is John Doe. I live in San Francisco."
    entities_to_censor = ['I-PER', 'B-PER', 'I-LOC', 'B-LOC']

    # Expected output after censoring 'John Doe' and 'San Francisco'
    expected_censored_text = "Hello, my name is ████ ███. I live in ███ █████████."

    censored_text = main.censor_hf(text, entities_to_censor, {'I-PER': 0})
    assert censored_text == expected_censored_text


def test_censor_hf_no_entities_to_censor(mocker, mock_nlp_hugging_face):
    mocker.patch('assignment1.main.recognize_entity', return_value=mock_nlp_hugging_face)
    text = "Hello, my name is John Doe. I live in San Francisco."
    entities_to_censor = []  # No entities to censor

    # Expected output should be the same as input text as no entities are censored
    expected_censored_text = text

    censored_text = main.censor_hf(text, entities_to_censor, {'I-PER': 0})
    assert censored_text == expected_censored_text


def test_censor_hf_no_entities_found(mocker):
    # Mock the Hugging Face model to return no entities
    mocker.patch('assignment1.main.recognize_entity', return_value=[])

    text = ">What other cool newsgroups are available for us alternative thinkers?"
    entities_to_censor = ['I-PER', 'B-PER', 'I-LOC', 'B-LOC']

    # Expected output should be the same as input text as no entities are found
    expected_censored_text = text

    censored_text = main.censor_hf(text, entities_to_censor, {'I-PER': 0})
    assert censored_text == expected_censored_text


@pytest.mark.parametrize("text, expected", [
    ("Bill Christensen", [("Bill Christensen", 0, 16)]),
    ("Thank you, Mr. Moore. I highly recommend the same.", [('Thank you', 0, 9), ('Mr. Moore', 11, 20),
                                                            ('I highly', 22, 30)]),
    ("(and we're open to more suggestions)", []),
    ("Concrete Research by David Moore", [('Concrete Research by', 0, 20), ('David Moore', 21, 32)]),
    ("worldnet.att.net (John E. Moore)", [("John E. Moore", 18, 31)]),
])
def test_check_entity_regex_name(text, expected):
    entity = 'NAME'
    result = main.check_entity_regex(text, entity)
    assert result == expected


def test_check_entity_regex_no_name():
    text = "We have a list of our favorites at"
    entity = 'NAME'
    expected = [('We have', 0, 7)]
    result = main.check_entity_regex(text, entity)
    assert result == expected


def test_check_entity_regex_unsupported_entity():
    text = "John Doe went to Paris."
    entity = 'LOCATION'  # Unsupported entity type
    expected = []
    result = main.check_entity_regex(text, entity)
    assert result == expected


def test_censor_regex_person(mocker, mock_another_recognize_entity):
    mocker.patch('assignment1.main.check_entity_regex', side_effect=lambda text, entity: {
        'NAME': [('John Doe', 7, 15)]
    }[entity])
    mocker.patch('assignment1.main.replace_with_black_block_by_indices',
                 side_effect=lambda text, start, end, word: text[:start] + '█' * (end - start) + text[end:])

    text = "Hello, John Doe. Your phone is 123-456-7890. The date is January 1, 2020."
    entities_to_censor = ['PERSON']
    expected_censored_text = "Hello, ████████. Your phone is 123-456-7890. The date is January 1, 2020."
    censored_text = main.censor_regex(text, entities_to_censor)
    assert censored_text == expected_censored_text


def test_censor_regex_phone(mocker):
    mocker.patch('assignment1.main.check_entity_regex', side_effect=lambda text, entity: {
        'PHONE': [('123-456-7890', 31, 43)]
    }[entity])
    mocker.patch('assignment1.main.replace_with_black_block_by_indices',
                 side_effect=lambda text, start, end, word: text[:start] + '█' * (end - start) + text[end:])

    text = "Hello, John Doe. Your phone is 123-456-7890. The date is January 1, 2020."
    entities_to_censor = ['PHONE']
    expected_censored_text = "Hello, John Doe. Your phone is ████████████. The date is January 1, 2020."
    censored_text = main.censor_regex(text, entities_to_censor)
    assert censored_text == expected_censored_text


def test_censor_regex_date(mocker):
    mocker.patch('assignment1.main.check_entity_regex', side_effect=lambda text, entity: {
        'DATE': [('January 1, 2020', 57, 72)]
    }[entity])
    mocker.patch('assignment1.main.replace_with_black_block_by_indices',
                 side_effect=lambda text, start, end, word: text[:start] + '█' * (end - start) + text[end:])

    text = "Hello, John Doe. Your phone is 123-456-7890. The date is January 1, 2020."
    entities_to_censor = ['DATE']
    expected_censored_text = "Hello, John Doe. Your phone is 123-456-7890. The date is ███████████████."
    censored_text = main.censor_regex(text, entities_to_censor)
    assert censored_text == expected_censored_text


def test_censor_regex_no_entity(mocker, mock_another_recognize_entity):
    mocker.patch('assignment1.main.check_entity_regex', side_effect=lambda text, entity: {
        'NAME': [('John Doe', 0, 8)],
        'PHONE': [('123-456-7890', 29, 41)],
        'DATE': [('January 1, 2020', 52, 67)],
        'ADDRESS': []
    }[entity])
    mocker.patch('assignment1.main.replace_with_black_block_by_indices',
                 side_effect=lambda text, start, end, word: text[:start] + '█' * (end - start) + text[end:])

    text = "Hello, John Doe. Your phone is 123-456-7890. The date is January 1, 2020."
    entities_to_censor = []
    expected_censored_text = text  # No change expected
    censored_text = main.censor_regex(text, entities_to_censor)
    assert censored_text == expected_censored_text


def test_write_censored_file(mocker, tmp_path):
    # Mock the open function
    mocked_open = mocker.patch('builtins.open', mock_open())

    # Define the censored text and the output file path
    censored_text = "This is censored content."
    output_file_path = tmp_path / "censored_file.txt"

    # Call the function
    main.write_censored_file(censored_text, str(output_file_path))

    # Check if the open function was called correctly
    mocked_open.assert_called_once_with(str(output_file_path), 'w', encoding='utf-8')

    # Check if the file.write was called with the correct text
    mocked_open().write.assert_called_once_with(censored_text)


def test_write_censored_file_content(tmp_path):
    # Define the censored text and the output file path
    censored_text = "This is censored content."
    output_file_path = tmp_path / "censored_file.txt"

    # Call the function
    main.write_censored_file(censored_text, str(output_file_path))

    # Read the file and check its content
    with open(output_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    assert content == censored_text



