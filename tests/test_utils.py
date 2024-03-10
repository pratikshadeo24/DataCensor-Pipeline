import sys
import pytest
from assignment1 import utils


@pytest.fixture
def mock_arg_parser(mocker):
    # Mock for arg_parser
    mock_parser = mocker.Mock()
    mock_parser.input = '/mock/input/path'
    mock_parser.output = '/mock/output/path'
    mock_parser.stats = 'stdout'
    return mock_parser


def test_output_stats_to_stderr(capsys):
    # Initialize
    stats = {"PERSON": 5, "DATE": 3}
    stats_output = "stderr"
    censored_file_path = "output/path/to/file.censored"

    # Expect
    expected_output = "File: output/path/to/file.censored\nPERSON: 5 occurrences\nDATE: 3 occurrences\n\n"

    # Execute
    utils.output_stats(stats, stats_output, censored_file_path)
    captured = capsys.readouterr()

    # Asserts
    assert captured.err == expected_output
    assert captured.out == ""


def test_output_stats_to_stdout(capsys):
    # Initialize
    stats = {"LOCATION": 2, "PHONE": 4}
    stats_output = "stdout"
    censored_file_path = "output/path/to/anotherfile.censored"

    # Expect
    expected_output = "File: output/path/to/anotherfile.censored\nLOCATION: 2 occurrences\nPHONE: 4 occurrences\n\n"

    # Execute
    utils.output_stats(stats, stats_output, censored_file_path)
    captured = capsys.readouterr()

    # Asserts
    assert captured.out == expected_output
    assert captured.err == ""


def test_output_stats_to_file(mocker):
    # Initialize
    stats = {"ORG": 1, "GPE": 2}
    stats_output = "output/path/to/stats.txt"
    censored_file_path = "output/path/to/file.censored"

    # Mock
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    # Expect
    expected_output = "File: output/path/to/file.censored\nORG: 1 occurrences\nGPE: 2 occurrences\n"

    # Execute
    utils.output_stats(stats, stats_output, censored_file_path)

    # Asserts
    mock_open.assert_called_once_with(stats_output, "w")
    mock_open().write.assert_called_once_with(expected_output + "\n")


def test_output_stats_file_error(mocker, capsys):
    # Initialize
    stats = {"LOC": 3}
    stats_output = "/invalid/path/to/stats.txt"
    censored_file_path = "output/path/to/file.censored"

    # Mock
    mocker.patch("builtins.open", side_effect=IOError("An error occurred"))

    # Execute
    utils.output_stats(stats, stats_output, censored_file_path)
    captured = capsys.readouterr()

    # Assert
    assert "An error occurred" in captured.out


def test_extract_arguments_all_arg_passed(mock_arg_parser):
    # Mock
    mock_arg_parser.names = True
    mock_arg_parser.dates = True
    mock_arg_parser.phones = True
    mock_arg_parser.address = True

    # Expect
    expected_entities = ["PERSON", "B-PER", "I-PER", "DATE", "PHONE", "ADDRESS", "B-LOC", "I-LOC", "GPE", "FAC", "LOC"]

    # Execute
    inp_path, out_path, out_stats, entities_to_censor = utils.extract_arguments(mock_arg_parser)

    # Asserts
    assert inp_path == '/mock/input/path'
    assert out_path == '/mock/output/path'
    assert out_stats == 'stdout'
    assert all(entity in entities_to_censor for entity in expected_entities)


def test_extract_arguments_no_arg_passed(mock_arg_parser):
    # Mock
    mock_arg_parser.names = False
    mock_arg_parser.dates = False
    mock_arg_parser.phones = False
    mock_arg_parser.address = False

    # Execute
    inp_path, out_path, out_stats, entities_to_censor = utils.extract_arguments(mock_arg_parser)

    # Asserts
    assert inp_path == '/mock/input/path'
    assert out_path == '/mock/output/path'
    assert out_stats == 'stdout'
    assert entities_to_censor == []


def test_extract_arguments_some_arg_passed(mock_arg_parser):
    # Mock
    mock_arg_parser.names = True
    mock_arg_parser.dates = False
    mock_arg_parser.phones = True
    mock_arg_parser.address = False

    # Expect
    expected_entities = ["PERSON", "B-PER", "I-PER", "PHONE"]

    # Execute
    inp_path, out_path, out_stats, entities_to_censor = utils.extract_arguments(mock_arg_parser)

    # Asserts
    assert inp_path == '/mock/input/path'
    assert out_path == '/mock/output/path'
    assert out_stats == 'stdout'
    assert all(entity in entities_to_censor for entity in expected_entities)


def test_parse_arguments_with_all_options(monkeypatch):
    # Initialize
    cli_args = ['program', '--input', 'sample/path/input.txt', '--names', '--dates', '--phones', '--address',
                '--output', 'output/', '--stats', 'stdout']

    # Mock
    monkeypatch.setattr(sys, 'argv', cli_args)

    # Execute
    args = utils.arguments_parser()

    # Asserts
    assert args.input == 'sample/path/input.txt'
    assert args.output == 'output/'
    assert args.stats == 'stdout'
    assert args.names is True
    assert args.dates is True
    assert args.phones is True
    assert args.address is True


def test_parse_arguments_with_minimum_required_options(monkeypatch):
    # Initialize
    cli_args = ['program', '--input', 'sample/path/input.txt', '--output', 'output/']

    # Mock
    monkeypatch.setattr(sys, 'argv', cli_args)

    # Execute
    args = utils.arguments_parser()

    # Asserts
    assert args.input == 'sample/path/input.txt'
    assert args.output == 'output/'
    assert args.stats is None
    assert args.names is False
    assert args.dates is False
    assert args.phones is False
    assert args.address is False


def test_parse_arguments_missing_required_options(monkeypatch):
    # Initialize
    test_args = ['program', '--output', 'output/']

    # Mock
    monkeypatch.setattr(sys, 'argv', test_args)

    # Assert
    with pytest.raises(SystemExit):
        # Execute
        utils.arguments_parser()
