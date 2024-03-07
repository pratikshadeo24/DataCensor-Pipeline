import argparse
from pathlib import Path
from glob import glob
import sys
from assignment1.main import write_censored_file, censor_regex, censor_hf, censor_spacy


def parse_arguments():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description='Censor sensitive information from text files.')

    # Define arguments that the script should accept
    parser.add_argument('--input', type=str, required=True, help='Input text files path.')
    parser.add_argument('--names', action='store_true', help='Flag to censor names.')
    parser.add_argument('--dates', action='store_true', help='Flag to censor dates.')
    parser.add_argument('--phones', action='store_true', help='Flag to censor phone numbers.')
    parser.add_argument('--address', action='store_true', help='Flag to censor addresses.')
    parser.add_argument('--output', type=str, required=True, help='Directory to store the censored files.')
    parser.add_argument('--stats', type=str, choices=['stderr', 'stdout'], help='Where to output the stats.')

    # Parse the command-line arguments
    return parser.parse_args()


def main(input_pattern, output_dir, entities_to_censor, stats_output):
    # Find all text files that match the input pattern
    files_to_censor = glob(input_pattern)

    # Process each file
    for file_path in files_to_censor:
        # Read the file
        print("Current file: ", Path(file_path))
        text = Path(file_path).read_text(encoding='utf-8')

        # Censor the text
        censored_text = censor_spacy(text, entities_to_censor)
        censored_text = censor_hf(censored_text, entities_to_censor)
        censored_text = censor_regex(censored_text, entities_to_censor)
        # Determine the output file path
        # censored_file_path = Path(output_dir) / (Path(file_path).stem + '.censored.txt')
        censored_file_path = f"{output_dir}{Path(file_path).stem}.censored"
        # Write the censored text to the output file
        write_censored_file(censored_text, censored_file_path)

        # Output the stats if required
        if stats_output == 'stderr':
            print(f"Censored entities in {file_path}", file=sys.stderr)
        elif stats_output == 'stdout':
            print(f"Censored entities in {file_path}", file=sys.stdout)


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Determine which entities to censor based on flags
    CENSOR_ENTITIES = []
    if args.names:
        CENSOR_ENTITIES.append('PERSON')
        CENSOR_ENTITIES.extend(['B-PER', 'I-PER'])
    if args.dates:
        CENSOR_ENTITIES.append('DATE')
    if args.phones:
        # Note: Implement custom logic for phone number recognition
        CENSOR_ENTITIES.append('PHONE')
    if args.address:
        # Note: Implement custom logic for address recognition
        CENSOR_ENTITIES.append('ADDRESS')
        CENSOR_ENTITIES.extend(['B-LOC', 'I-LOC'])
        # CENSOR_ENTITIES.extend(['GPE', 'ORG', 'FAC', 'LOC'])

    # Process the files with the specified censorship criteria
    main(args.input, args.output, CENSOR_ENTITIES, args.stats)
