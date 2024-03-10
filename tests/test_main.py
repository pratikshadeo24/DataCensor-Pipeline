import pytest
from unittest.mock import mock_open
from assignment1 import main


@pytest.fixture
def mock_recognize_entity(mocker):
    # Mock the recognize_entity function
    mock_rec_ent = mocker.patch('assignment1.main.recognize_entity')

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

    mock_rec_ent.return_value = mock_doc()
    return mock_rec_ent


@pytest.fixture
def mock_nlp_hugging_face():
    # Mock the Hugging Face model's output
    return [
        {'entity': 'I-PER', 'start': 18, 'end': 22},
        {'entity': 'B-PER', 'start': 23, 'end': 26},
        {'entity': 'I-LOC', 'start': 38, 'end': 41},
        {'entity': 'B-LOC', 'start': 42, 'end': 51}
    ]


@pytest.fixture
def mock_spacy_doc(mocker):
    # Create a mock Spacy doc
    mocked_nlp_spacy = mocker.Mock()
    mocked_doc = mocker.Mock()
    mocked_nlp_spacy.return_value = mocked_doc
    mocked_doc.ents = [mocker.Mock(text='John Doe', label_='PERSON')]
    return mocked_nlp_spacy


def test_recognize_entity_spacy(mocker):
    # Mocks
    mocked_nlp = mocker.Mock()
    mocked_doc = mocker.Mock()
    mocked_nlp.return_value = mocked_doc
    mocked_doc.ents = ['PERSON', 'DATE']

    # Execute
    text = "Sample text for testing"
    result = main.recognize_entity(mocked_nlp, text)

    # Asserts
    mocked_nlp.assert_called_once_with(text)
    assert result == mocked_doc


def test_recognize_entity_huggingface(mocker):
    # Mocks
    mocked_nlp = mocker.Mock()
    mocked_output = {'entities': ['PER', 'LOC']}
    mocked_nlp.return_value = mocked_output

    # Execute
    text = "Sample text for testing"
    result = main.recognize_entity(mocked_nlp, text)

    # Asserts
    mocked_nlp.assert_called_once_with(text)
    assert result == mocked_output


@pytest.mark.parametrize("text, start, end, expected", [
    ("Hello James", 6, 11, "Hello █████"),
    ("Please contact me at 1234-5678", 21, 30, "Please contact me at █████████"),
    ("Allen is at the start", 0, 5, "█████ is at the start"),
    ("See you later in the office, Bob", 29, 32, "See you later in the office, ███"),
])
def test_replace_with_black_block_by_indices(text, start, end, expected):
    # Execute
    censored_text = main.replace_with_black_block_by_indices(text, start, end)

    # Assert
    assert censored_text == expected


def test_censor_with_spacy_correct_entities(mock_recognize_entity):
    # Initialize
    text = "John Doe's phone number is 123456789."
    entities_to_censor = ['PERSON', 'PHONE']

    # Execute
    censored_text = main.censor_with_spacy(text, entities_to_censor, {'PERSON': {'count': 0, 'indices': []}})

    # Assert
    assert censored_text == "████████'s phone number is █████████."


def test_censor_with_spacy_ignores_uncensored_entities(mock_recognize_entity):
    # Initialize
    text = "John Doe lives in New York."
    entities_to_censor = ['PHONE']  # Not censoring 'PERSON' or 'GPE'

    # Execute
    censored_text = main.censor_with_spacy(text, entities_to_censor, {})

    # Assert
    assert censored_text == "John Doe lives in New York."


def test_censor_with_spacy_no_entities_to_censor(mock_recognize_entity):
    # Initialize
    text = "Just a plain sentence with no entities."
    entities_to_censor = []

    # Execute
    censored_text = main.censor_with_spacy(text, entities_to_censor, {'PERSON': 0})

    # Assert
    assert censored_text == text


def test_censor_with_hf_entities(mocker, mock_nlp_hugging_face):
    # Initialize
    text = "Hello, my name is John Doe. I live in San Francisco."
    entities_to_censor = ['I-PER', 'B-PER', 'I-LOC', 'B-LOC']

    # Mock
    mocker.patch('assignment1.main.recognize_entity', return_value=mock_nlp_hugging_face)

    # Expect
    expected_censored_text = "Hello, my name is ████ ███. I live in ███ █████████."

    # Execute
    censored_text = main.censor_with_hf(text, entities_to_censor, {'I-PER': 0})

    # Assert
    assert censored_text == expected_censored_text


def test_censor_with_hf_no_entities_to_censor(mocker, mock_nlp_hugging_face):
    # Initialize
    text = "Hello, my name is John Doe. I live in San Francisco."
    entities_to_censor = []

    # Mock
    mocker.patch('assignment1.main.recognize_entity', return_value=mock_nlp_hugging_face)

    # Expect
    expected_censored_text = text

    # Execute
    censored_text = main.censor_with_hf(text, entities_to_censor, {'I-PER': 0})

    # Assert
    assert censored_text == expected_censored_text


def test_censor_with_hf_no_entities_found(mocker):
    # Initialize
    text = ">What other cool newsgroups are available for us alternative thinkers?"
    entities_to_censor = ['I-PER', 'B-PER', 'I-LOC', 'B-LOC']

    # Mock
    mocker.patch('assignment1.main.recognize_entity', return_value=[])

    # Expect
    expected_censored_text = text

    # Execute
    censored_text = main.censor_with_hf(text, entities_to_censor, {'I-PER': 0})

    # Assert
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
    # Initialize
    entity = 'NAME'

    # Execute
    result = main.check_entity_regex(text, entity)

    # Assert
    assert result == expected


def test_check_entity_regex_no_name():
    # Initialize
    text = "We have a list of our favorites at"
    entity = 'NAME'

    # Expect
    expected = [('We have', 0, 7)]

    # Execute
    result = main.check_entity_regex(text, entity)

    # Assert
    assert result == expected


def test_check_entity_regex_unsupported_entity():
    # Initialize
    text = "John Doe went to Paris."
    entity = 'LOCATION'

    # Expect
    expected = []

    # Execute
    result = main.check_entity_regex(text, entity)

    # Assert
    assert result == expected


def test_censor_with_regex_person(mocker, mock_spacy_doc):
    # Mocks
    mocker.patch('assignment1.main.check_entity_regex', side_effect=lambda text, entity: {
        'NAME': [('John Doe', 7, 15)]
    }[entity])
    mocker.patch('assignment1.main.replace_with_black_block_by_indices',
                 side_effect=lambda text, start, end, word: text[:start] + '█' * (end - start) + text[end:])

    # Initialize
    text = "Hello, John Doe. Your phone is 123-456-7890. The date is January 1, 2020."
    entities_to_censor = ['PERSON']

    # Expect
    expected_censored_text = "Hello, ████████. Your phone is 123-456-7890. The date is January 1, 2020."

    # Execute
    censored_text = main.censor_with_regex(text, entities_to_censor)

    # Assert
    assert censored_text == expected_censored_text


def test_censor_with_regex_no_entity(mocker, mock_spacy_doc):
    # Mocks
    mocker.patch('assignment1.main.check_entity_regex', side_effect=lambda text, entity: {
        'NAME': [('John Doe', 0, 8)],
        'PHONE': [('123-456-7890', 29, 41)],
        'DATE': [('January 1, 2020', 52, 67)],
        'ADDRESS': []
    }[entity])
    mocker.patch('assignment1.main.replace_with_black_block_by_indices',
                 side_effect=lambda text, start, end, word: text[:start] + '█' * (end - start) + text[end:])

    # Initialize
    text = "Hello, John Doe. Your phone is 123-456-7890. The date is January 1, 2020."
    entities_to_censor = []

    # Expect
    expected_censored_text = text

    # Execute
    censored_text = main.censor_with_regex(text, entities_to_censor)

    # Assert
    assert censored_text == expected_censored_text


def test_write_censored_file(mocker, tmp_path):
    # Mock
    mocked_open = mocker.patch('builtins.open', mock_open())

    # Initialize
    censored_text = "This is censored content."
    output_file_path = tmp_path / "censored_file.txt"

    # Execute
    main.write_censored_file(censored_text, str(output_file_path))

    # Asserts
    mocked_open.assert_called_once_with(str(output_file_path), 'w', encoding='utf-8')
    mocked_open().write.assert_called_once_with(censored_text)


def test_write_censored_file_content(tmp_path):
    # Initialize
    censored_text = "This is censored content."
    output_file_path = tmp_path / "censored_file.txt"

    # Execute
    main.write_censored_file(censored_text, str(output_file_path))

    # Read the file and check its content
    with open(output_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Assert
    assert content == censored_text
