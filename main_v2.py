import re

import spacy
import argparse
from pathlib import Path
from glob import glob
import sys
import json
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline


# Load SpaCy model
nlp_spacy = spacy.load("en_core_web_lg")
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
nlp_hugging_face = pipeline("ner", model=model, tokenizer=tokenizer)


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


def recognize_entity(nlp_model, text):
    return nlp_model(text)


def replace_with_black_block_by_indices(text, start, end, word):
    # Calculate the length of the substring to be replaced
    length = end - start

    # Replace the substring with black blocks
    censored_text = text[:start] + ('█' * length) + text[end:]
    print("Censored the word: ", word)
    return censored_text


def censor_spacy(text, entities_to_censor, word=None):
    # Process the text with SpaCy
    doc = recognize_entity(nlp_spacy, text)

    censored_text = text
    for ent in doc.ents:
        en_label = ent.label_
        if en_label in entities_to_censor:
            censored_text = censored_text.replace(ent.text, '█' * len(ent.text))

    return censored_text


def censor_hf(text, entities_to_censor):
    # Process the text with Hugging face
    doc = recognize_entity(nlp_hugging_face, text)

    # Convert text to list of characters
    censored_text_list = list(text)

    # Iterate over the named entities and censor them
    for ner in doc:
        if ner['entity'] in entities_to_censor:
            start_idx = ner['start']
            # Replace characters within the entity with blocks
            i = start_idx
            while censored_text_list[i].isalpha():
                censored_text_list[i] = '█'
                i += 1

    return ''.join(censored_text_list)


def check_names_regex(text):
    name_regex = r"\b(?:(?:[A-Z][a-z]+,?\s)?[A-Z][a-z]*\.?(?:\s|\s?[A-Z][-])?[A-Z]?[a-z]*\.?|[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?(?:\s[A-Z]\.?\s?[A-Z]?[a-z]*\.?)?)\b"

    output = []
    for match in re.finditer(name_regex, text):
        # Extract the matched word
        matched_word = match.group()
        # Get the start index of the matched word
        start_index = match.start()
        # Calculate the length of the matched word
        end_index = match.end()
        # Append the tuple (matched_word, start_index, word_length) to the output list
        output.append((matched_word, str(start_index), str(end_index)))

    return output


def censor_regex(text, entities_to_censor):
    censored_text = text
    name_regex_list = check_names_regex(text)
    for ent in name_regex_list:
        # Parse with Hugging face
        # parsed_words = recognize_entity(nlp_hugging_face, ent[0])
        # if parsed_words:
        #     for entity in parsed_words:
        #         if entity['entity'] in entities_to_censor:
        #             censored_text = replace_with_black_block_by_indices(censored_text, int(ent[1]), int(ent[2]), ent[0])

        # Parse with Spacy
        parsed_word = recognize_entity(nlp_spacy, ent[0])
        for par_ent in parsed_word.ents:
            en_label = par_ent.label_
            if en_label in entities_to_censor:
                censored_text = censored_text.replace(par_ent.text, '█' * len(par_ent.text))
        # censored_text = censor_spacy(ent, entities_to_censor)

    return censored_text


def write_censored_file(censored_text, output_file_path):
    # Write the censored text to a new file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(censored_text)


def process_files(input_pattern, output_dir, entities_to_censor, stats_output):
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
        censored_file_path = f"{output_dir}{Path(file_path).stem}reghugspy.txt"
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

    # Process the files with the specified censorship criteria
    process_files(args.input, args.output, CENSOR_ENTITIES, args.stats)
