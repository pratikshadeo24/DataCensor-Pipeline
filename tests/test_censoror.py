import pytest
import sys
from censoror import main, parse_arguments


# Fixture to mock Path.read_text
@pytest.fixture
def mock_read_text(mocker):
    return mocker.patch('censoror.Path.read_text', return_value='Sample text')


# Fixture to mock glob function
@pytest.fixture
def mock_glob(mocker):
    sample_paths = ['/sample/mock/path/file1.txt', '/sample/mock/path/file2.txt']
    return mocker.patch('censoror.glob', return_value=sample_paths)


# Fixture to mock write_censored_file function
@pytest.fixture
def mock_write_censored_file(mocker):
    return mocker.patch('censoror.write_censored_file')


# Fixture to mock censoring functions
@pytest.fixture
def mock_censor_functions(mocker, stats=None):
    mocker.patch('censoror.censor_spacy', side_effect=lambda text, entities, stats: text.replace('text', 'tx'))
    mocker.patch('censoror.censor_hf', side_effect=lambda text, entities, stats: text.replace('tx', 't*'))
    mocker.patch('censoror.censor_regex', side_effect=lambda text, entities: text.replace('t*', '***'))
    mocker.patch('censoror.output_stats', return_value=True)


def test_parse_arguments_with_all_options(monkeypatch):
    test_args = [
        'program',
        '--input', 'input.txt',
        '--names',
        '--dates',
        '--phones',
        '--address',
        '--output', 'output/',
        '--stats', 'stdout'
    ]

    monkeypatch.setattr(sys, 'argv', test_args)
    args = parse_arguments()

    assert args.input == 'input.txt'
    assert args.names is True
    assert args.dates is True
    assert args.phones is True
    assert args.address is True
    assert args.output == 'output/'
    assert args.stats == 'stdout'


def test_parse_arguments_with_minimum_required_options(monkeypatch):
    test_args = [
        'program',  # Simulating program name
        '--input', 'input.txt',
        '--output', 'output/'
    ]

    monkeypatch.setattr(sys, 'argv', test_args)
    args = parse_arguments()

    assert args.input == 'input.txt'
    assert args.names is False
    assert args.dates is False
    assert args.phones is False
    assert args.address is False
    assert args.output == 'output/'
    assert args.stats is None


def test_parse_arguments_missing_required_options(monkeypatch):
    test_args = [
        'program',  # Simulating program name
        '--output', 'output/'
    ]

    # Expect the function to raise a SystemExit exception due to missing required arguments
    monkeypatch.setattr(sys, 'argv', test_args)
    with pytest.raises(SystemExit):
        parse_arguments()


# def test_main_all_functions_called(mock_glob, mock_read_text, mock_write_censored_file, mock_censor_functions, capsys):
#     main('*.txt', '/output/dir/', ['PERSON', 'LOCATION'], 'stdout')
#
#     # Check if glob was called correctly
#     mock_glob.assert_called_once_with('*.txt')
#
#     assert mock_read_text.call_count == 2
#
#     # Check if write_censored_file was called correctly
#     mock_write_censored_file.assert_any_call('Sample ***', '/output/dir/file1.censored')
#     mock_write_censored_file.assert_any_call('Sample ***', '/output/dir/file2.censored')
#
#     # Check if stats were printed to stdout
#     captured = capsys.readouterr()
#     assert "Current file:  /sample/mock/path/file1.txt" in captured.out
#     assert "Current file:  /sample/mock/path/file2.txt" in captured.out


# def test_main_stderr_output(mock_glob, mock_read_text, mock_write_censored_file, mock_censor_functions, capsys):
#     main('*.txt', '/output/dir/', ['PERSON', 'LOCATION'], 'stderr')
#
#     # Check stderr output
#     captured = capsys.readouterr()
#     # assert 'Censored entities in /sample/mock/path/file1.txt' in captured.err
#     # assert 'Censored entities in /sample/mock/path/file2.txt' in captured.err
#     assert "Current file:  /sample/mock/path/file1.txt" in captured.out
#     assert "Current file:  /sample/mock/path/file2.txt" in captured.out

