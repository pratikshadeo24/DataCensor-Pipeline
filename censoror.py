from glob import glob
from pathlib import Path
from assignment1.utils import output_stats, extract_arguments, arguments_parser
from assignment1.main import censor_with_spacy, censor_with_hf, censor_with_regex, write_censored_file


def main(input_pattern, output_dir, entities_to_censor, stats_output):
    # Find all text files
    files_to_censor = glob(input_pattern)

    # Process each file
    for file_path in files_to_censor:
        # Read a specific file
        print("Current file: ", Path(file_path))
        try:
            text_to_process = Path(file_path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

        stats = {}

        # Process text with different models
        censored_text = censor_with_spacy(text_to_process, entities_to_censor, stats)  # censor by Spacy
        censored_text = censor_with_hf(censored_text, entities_to_censor, stats)  # censor by Hugging face
        censored_text = censor_with_regex(censored_text, entities_to_censor)  # censor by Regex and Spacy

        # Create censored output file
        censored_file_path = Path(output_dir) / (Path(file_path).stem + ".censored")
        write_censored_file(censored_text, censored_file_path)

        # Stats for output
        output_stats(stats, stats_output, censored_file_path)


if __name__ == "__main__":
    # Parse all command-line arguments
    args = arguments_parser()

    input_path, output_path, out_stats, censor_entities = extract_arguments(args)

    # Process the files with the specified censorship criteria
    main(input_path, output_path, censor_entities, out_stats)

