import argparse
import sys


# Pattern for identifying phone number in different formats
phone_patterns = [
    # Format: 123-456-7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3},
                                   {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: (123) 456-7890
    {"label": "PHONE", "pattern": [{"ORTH": "("}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ")"},
                                   {"IS_SPACE": True, "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"},
                                   {"IS_DIGIT": True, "LENGTH": 4}]},
    # format: +1 123-456-7890
    {"label": "PHONE", "pattern": [{"ORTH": "+"}, {"IS_DIGIT": True, "LENGTH": 1}, {"IS_SPACE": True},
                                   {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3},
                                   {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: 1-123-456-7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 1}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3},
                                   {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"},
                                   {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: 123.456.7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ".", "OP": "?"},
                                   {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ".", "OP": "?"},
                                   {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: 123 456 7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 3}, {"IS_SPACE": True}, {"IS_DIGIT": True, "LENGTH": 3},
                                   {"IS_SPACE": True}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: 512) 263-0177
    # Assumption: a starting '(' is missing, making it optional.
    {"label": "PHONE", "pattern": [{"ORTH": "(", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ")"},
                                   {"IS_SPACE": True, "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"},
                                   {"IS_DIGIT": True, "LENGTH": 4}]},
]

# Pattern for identifying dates in different formats
date_patterns = [
    # Format: 14 May 2001
    {"label": "DATE", "pattern": [{"SHAPE": "dd"}, {"IS_ALPHA": True}, {"SHAPE": "dddd"}]},
    # Format: 05/03/2001
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},
    # Format: April 18, 2001
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"SHAPE": "dd, "}, {"SHAPE": "dddd"}]},
    # Format: Dec/13/2000
    {"label": "DATE", "pattern": [{"LOWER": {"IN": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
                                                    "oct", "nov", "dec"]}}, {"ORTH": "/"},
                                  {"IS_DIGIT": True, "LENGTH": 2}, {"ORTH": "/"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: january 01, 2020
    {"label": "DATE", "pattern": [{"LOWER": {"IN": ["january", "february", "march", "april", "may", "june", "july",
                                                    "august", "september", "october", "november", "december"]}},
                                  {"IS_DIGIT": True, "LENGTH": 2}, {"ORTH": ","}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: mar 15, 2021
    {"label": "DATE", "pattern": [{"LOWER": {"IN": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sept",
                                                    "oct", "nov", "dec"]}}, {"IS_DIGIT": True, "LENGTH": 2},
                                  {"ORTH": ","}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # Format: Dec. 15
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"ORTH": "."}, {"SHAPE": "dd"}]},
    # Format: 12/13/2000
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},
    # Format: February 12
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"SHAPE": "dd"}]},
    # Format: 10/11/01
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dd"}]},
    # Format: 13/05/2001
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},
    # Format: Jan 18, 2001
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"SHAPE": "dd,"}, {"SHAPE": "dddd"}]}
]


def output_stats(stats, stats_output, censored_file_path):
    # Construct stats message
    stats_message = f"File: {censored_file_path}\n"
    for entity, count in stats.items():
        stats_message += f"{entity}: {count} occurrences\n"

    # Determine the output destination
    if stats_output == "stderr":
        print(stats_message, file=sys.stderr)
    elif stats_output == "stdout":
        print(stats_message, file=sys.stdout)
    else:  # Output to a file
        try:
            with open(stats_output, "w") as file:
                file.write(stats_message + "\n")
        except IOError as e:
            print(f"An error occurred while writing to the file: {e}")


def extract_arguments(arg_parser):
    # Determine which entities to censor based on flags
    entities_to_censor = []
    if arg_parser.names:
        entities_to_censor.extend(["PERSON", "B-PER", "I-PER"])
    if arg_parser.dates:
        entities_to_censor.append("DATE")
    if arg_parser.phones:
        entities_to_censor.append("PHONE")
    if arg_parser.address:
        entities_to_censor.extend(["ADDRESS", "B-LOC", "I-LOC", "GPE", "FAC", "LOC"])

    inp_path = arg_parser.input
    out_path = arg_parser.output
    out_stats = arg_parser.stats

    return inp_path, out_path, out_stats, entities_to_censor


def arguments_parser():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Censor sensitive information from text files.")

    # Define all arguments that the script should accept
    parser.add_argument("--input", type=str, required=True,
                        help="Input path. Could be a single file or folder.")
    parser.add_argument("--names", action="store_true", help="Name censor flag.")
    parser.add_argument("--dates", action="store_true", help="Date censor flag.")
    parser.add_argument("--phones", action="store_true", help="Phone Number censor flag.")
    parser.add_argument("--address", action="store_true", help="Address censor flag.")
    parser.add_argument("--output", type=str, required=True,
                        help="Path or Directory to store the censored files.")
    parser.add_argument("--stats", type=str,
                        help='File or stream to output the stats. Use "stderr" or "stdout" for console output or '
                             'provide a file path to write to a file.',
                        )

    # Parse the command-line arguments
    return parser.parse_args()

