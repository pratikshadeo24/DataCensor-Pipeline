import re
import spacy
import argparse
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline


# Load SpaCy model
nlp_spacy = spacy.load("en_core_web_sm")
# Load Hugging face model
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
nlp_hugging_face = pipeline("ner", model=model, tokenizer=tokenizer)

ruler = nlp_spacy.add_pipe("entity_ruler", before="ner")

phone_patterns = [{"label": "PHONE_NUMBER", "pattern": [{"ORTH": "("}, {"IS_DIGIT": True, "LENGTH": {"==": 3}}, {"ORTH": ")"}, {"IS_DIGIT": True, "LENGTH": {"==": 3}}, {"ORTH": "-", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": {"==": 4}}]},  # (123) 4567 or (123)-4567
    {"label": "PHONE_NUMBER", "pattern": [{"IS_DIGIT": True, "LENGTH": {"==": 3}}, {"ORTH": "-", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": {"==": 3}}, {"ORTH": "-", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": {"==": 4}}]},  # 123-456-7890
    {"label": "PHONE_NUMBER", "pattern": [{"IS_DIGIT": True, "LENGTH": {"==": 4}}, {"ORTH": "-", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": {"==": 4}}]},  # 1234-5678
    {"label": "PHONE_NUMBER", "pattern": [{"IS_DIGIT": True, "LENGTH": {"==": 3}}, {"ORTH": ".", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": {"==": 3}}, {"ORTH": ".", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": {"==": 4}}]},  # 123.456.7890
    ]
ruler.add_patterns(phone_patterns)


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


def check_entity_regex(text, entity):
    if entity == 'NAME':
        ent_regex = (r"\b(?:(?:[A-Z][a-z]+,?\s)?[A-Z][a-z]*\.?(?:\s|\s?[A-Z][-])?[A-Z]?[a-z]*\.?|[A-Z][a-z]+(?:[-']["
                     r"A-Z][a-z]+)?(?:\s[A-Z]\.?\s?[A-Z]?[a-z]*\.?)?)\b")
    else:
        return []
    # elif entity == 'DATE':
    #     ent_regex = (r'(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[13-9]|1[0-2])\2))(?:(?:1['
    #                  r'6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|['
    #                  r'13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:(?:0?['
    #                  r'1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})')
    # elif entity == 'PHONE':
    #     # ent_regex = (r"(?:\+1\s*(?:[.-]\s*)?)?(?:\(\s*(\d{3})\s*\)|(\d{3}))[\s.-]?(\d{3})[\s.-]?(\d{4})(?:\s*("
    #     #              r"?:ext\.?|x)\s*(\d{2,5}))?")
    #     ent_regex = r"\b(\d{3}[-.]\d{3}[-.]\d{4}|\d{3}[-. ]?\(\d{3}\)[-.]?\d{4}|\d{3}[-. ]?\(\d{3}\)[-. ]?\d{4})\b"
    #     ent_regex = r"\b(\d{3}[-.]\d{3}[-.]\d{4}|\d{3}[-. ]?\(?\d{3}\)?[-.]?\d{4}|\d{3}[-. ]?\(?\d{3}\)?[-. ]?\d{4})\b"
    # else:
    #     ent_regex = (r"\b\d{1,5}\s+\w+(\s+\w+)(?:\s+(Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln"
    #                  r"|Circle|Cir))?(?:,\s(?:[A-Z]{2}))?\s+\d{5}(-\d{4})?\b")

    output = []
    for match in re.finditer(ent_regex, text):
        # Extract the matched word
        matched_word = match.group()
        # Get the start index of the matched word
        start_index = match.start()
        # Calculate the length of the matched word
        end_index = match.end()
        # Append the tuple (matched_word, start_index, word_length) to the output list
        output.append((matched_word, int(start_index), int(end_index)))

    return output


def censor_regex(text, entities_to_censor):
    censored_text = text
    if 'PERSON' in entities_to_censor:
        name_regex_list = check_entity_regex(text, 'NAME')
        for ent in name_regex_list:
            # Parse with Hugging face parsed_words = recognize_entity(nlp_hugging_face, ent[0]) if parsed_words: for
            # entity in parsed_words: if entity['entity'] in entities_to_censor: censored_text =
            # replace_with_black_block_by_indices(censored_text, int(ent[1]), int(ent[2]), ent[0])

            # Parse with Spacy
            parsed_word = recognize_entity(nlp_spacy, ent[0])
            for par_ent in parsed_word.ents:
                en_label = par_ent.label_
                if en_label in entities_to_censor:
                    censored_text = censored_text.replace(par_ent.text, '█' * len(par_ent.text))
            # censored_text = censor_spacy(ent, entities_to_censor)
    if 'PHONE' in entities_to_censor:
        phone_regex_list = check_entity_regex(censored_text, 'PHONE')
        for phone in phone_regex_list:
            censored_text = replace_with_black_block_by_indices(censored_text, phone[1], phone[2], phone[0])
    if 'DATE' in entities_to_censor:
        date_regex_list = check_entity_regex(censored_text, 'DATE')
        for date_ent in date_regex_list:
            censored_text = replace_with_black_block_by_indices(censored_text, date_ent[1], date_ent[2], date_ent[0])
    if 'ADDRESS' in entities_to_censor:
        address_regex_list = check_entity_regex(censored_text, 'ADDRESS')
        for address in address_regex_list:
            censored_text = replace_with_black_block_by_indices(censored_text, address[1], address[2], address[0])

    return censored_text


def write_censored_file(censored_text, output_file_path):
    # Write the censored text to a new file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        print("aaaa: ", output_file_path)
        file.write(censored_text)

