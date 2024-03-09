import re
import spacy
import argparse
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline


# Load SpaCy model
nlp_spacy = spacy.load("en_core_web_md")
# Load Hugging face model
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
nlp_hugging_face = pipeline("ner", model=model, tokenizer=tokenizer)
# hf_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", aggregation_strategy="simple")

ruler = nlp_spacy.add_pipe("entity_ruler", before="ner")

phone_patterns = [
    # 123-456-7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # (123) 456-7890
    {"label": "PHONE", "pattern": [{"ORTH": "("}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ")"}, {"IS_SPACE": True, "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # +1 123-456-7890
    {"label": "PHONE", "pattern": [{"ORTH": "+"}, {"IS_DIGIT": True, "LENGTH": 1}, {"IS_SPACE": True}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # 1-123-456-7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 1}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # 123.456.7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ".", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ".", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # 123 456 7890
    {"label": "PHONE", "pattern": [{"IS_DIGIT": True, "LENGTH": 3}, {"IS_SPACE": True}, {"IS_DIGIT": True, "LENGTH": 3}, {"IS_SPACE": True}, {"IS_DIGIT": True, "LENGTH": 4}]},
    # 512) 263-0177 (Assuming a starting '(' is missing, making it optional)
    {"label": "PHONE", "pattern": [{"ORTH": "(", "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": ")"}, {"IS_SPACE": True, "OP": "?"}, {"IS_DIGIT": True, "LENGTH": 3}, {"ORTH": "-"}, {"IS_DIGIT": True, "LENGTH": 4}]},
]

date_patterns = [
    {"label": "DATE", "pattern": [{"SHAPE": "dd"}, {"IS_ALPHA": True}, {"SHAPE": "dddd"}]},  # 14 May 2001
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},  # 05/03/2001
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"SHAPE": "dd, "}, {"SHAPE": "dddd"}]},  # April 18, 2001
    {"label": "DATE", "pattern": [{"LOWER": {"IN": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]}}, {"ORTH": "/"}, {"IS_DIGIT": True, "LENGTH": 2}, {"ORTH": "/"}, {"IS_DIGIT": True, "LENGTH": 4}]},  # Dec/13/2000
    {"label": "DATE", "pattern": [{"LOWER": {"IN": ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]}}, {"IS_DIGIT": True, "LENGTH": 2}, {"ORTH": ","}, {"IS_DIGIT": True, "LENGTH": 4}]},
    {"label": "DATE", "pattern": [{"LOWER": {"IN": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sept", "oct", "nov", "dec"]}}, {"IS_DIGIT": True, "LENGTH": 2}, {"ORTH": ","}, {"IS_DIGIT": True, "LENGTH": 4}]},
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"ORTH": "."}, {"SHAPE": "dd"}]},  # Dec. 15
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},  # 12/13/2000
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"SHAPE": "dd"}]},  # February 12
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dd"}]},  # 10/11/01
    {"label": "DATE", "pattern": [{"SHAPE": "dd/dd/dddd"}]},  # 13/05/2001
    {"label": "DATE", "pattern": [{"IS_ALPHA": True}, {"SHAPE": "dd,"}, {"SHAPE": "dddd"}]},  # Jan 18, 2001
]
ruler.add_patterns(phone_patterns)
ruler.add_patterns(date_patterns)


def recognize_entity(nlp_model, text):
    return nlp_model(text)


def replace_with_black_block_by_indices(text, start, end, word):
    # Calculate the length of the substring to be replaced
    length = end - start

    # Replace the substring with black blocks
    censored_text = text[:start] + ('█' * length) + text[end:]
    print("Censored the word: ", word)
    return censored_text


def censor_spacy(text, entities_to_censor, stats):
    # Process the text with SpaCy
    doc = recognize_entity(nlp_spacy, text)

    censored_text = text
    for ent in doc.ents:
        en_label = ent.label_
        if en_label in entities_to_censor:
            censored_text = censored_text.replace(ent.text, '█' * len(ent.text))

            # Update stats
            entity_label = ent.label_
            if entity_label in stats:
                stats[entity_label]['count'] += 1
                stats[entity_label]['indices'].append((ent.start_char, ent.end_char))
            else:
                stats[entity_label] = {'count': 1, 'indices': [(ent.start_char, ent.end_char)]}
    return censored_text


def censor_hf(text, entities_to_censor, stats):
    # Process the text with Hugging face
    doc = recognize_entity(nlp_hugging_face, text)

    # Convert text to list of characters
    censored_text_list = list(text)

    # Iterate over the named entities and censor them
    for ner in doc:
        entity_type = ner['entity']
        if entity_type in entities_to_censor:
            # Update the count in stats
            if entity_type not in stats:
                stats[entity_type] = 0
            stats[entity_type] += 1

            start_idx = ner['start']
            # Replace characters within the entity with blocks
            i = start_idx
            while censored_text_list[i].isalpha():
                censored_text_list[i] = '█'
                i += 1

    return ''.join(censored_text_list)

# def censor_hf(text, entities_to_censor):
#     # Process the text with the updated Hugging Face model
#     doc = hf_pipeline(text)
#
#     # Iterate over the detected entities and censor them
#     censored_text = text
#     for entity in doc:
#         # Check if the entity is among the types we want to censor
#         if entity['entity_group'] in entities_to_censor:
#             start, end = entity['start'], entity['end']
#             # Replace the entity with a block of █ characters
#             censored_text = censored_text[:start] + '█' * (end - start) + censored_text[end:]
#
#     return censored_text


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

