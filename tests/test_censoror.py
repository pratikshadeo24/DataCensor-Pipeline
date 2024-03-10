import pytest
from pathlib import Path
from censoror import main


@pytest.fixture
def mock_read_text(mocker):
    # Mock Path.read_text
    return mocker.patch('censoror.Path.read_text', return_value='Sample text')


@pytest.fixture
def mock_glob(mocker):
    # Mock glob function
    sample_paths = ['/sample/mock/path/file1.txt', '/sample/mock/path/file2.txt']
    return mocker.patch('censoror.glob', return_value=sample_paths)


@pytest.fixture
def mock_write_censored_file(mocker):
    # Mock write_censored_file function
    return mocker.patch('censoror.write_censored_file')


@pytest.fixture
def mock_censor_functions(mocker, stats=None):
    # Mock censoring functions
    mocker.patch('censoror.censor_with_spacy', side_effect=lambda text, entities, stats: text.replace('text', 'tx'))
    mocker.patch('censoror.censor_with_hf', side_effect=lambda text, entities, stats: text.replace('tx', 't*'))
    mocker.patch('censoror.censor_with_regex', side_effect=lambda text, entities: text.replace('t*', '***'))
    mocker.patch('censoror.output_stats', return_value=True)


def test_main_empty_input(mock_write_censored_file):
    # Execute
    main('', '/output/', ['PERSON', 'LOCATION'], 'stdout')

    # Assert
    mock_write_censored_file.assert_not_called()


def test_main(mock_glob, mock_read_text, mock_write_censored_file, mock_censor_functions, capsys):
    # Execute
    main('*.txt', '/output/', ['PERSON', 'LOCATION'], 'stdout')

    # Asserts
    # Check if glob was called correctly
    mock_glob.assert_called_once_with('*.txt')
    assert mock_read_text.call_count == 2
    # Check if write_censored_file was called correctly
    mock_write_censored_file.assert_any_call('Sample ***', Path('/output/file1.censored'))
    mock_write_censored_file.assert_any_call('Sample ***', Path('/output/file2.censored'))

    # Check if stats were printed to stdout
    captured = capsys.readouterr()
    # Check the printed output
    assert "Current file:  /sample/mock/path/file1.txt" in captured.out
    assert "Current file:  /sample/mock/path/file2.txt" in captured.out


def test_main_stderr_output(mock_glob, mock_read_text, mock_write_censored_file, mock_censor_functions, capsys):
    # Execute
    main('*.txt', '/output/dir/', ['PERSON', 'LOCATION'], 'stderr')

    # Check stderr output
    captured = capsys.readouterr()

    # Asserts
    assert "Current file:  /sample/mock/path/file1.txt" in captured.out
    assert "Current file:  /sample/mock/path/file2.txt" in captured.out

