import re
import spacy
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from assignment1.utils import phone_patterns, date_patterns


# Load SpaCy model
nlp_spacy = spacy.load("en_core_web_md")
ruler = nlp_spacy.add_pipe("entity_ruler", before="ner")
ruler.add_patterns(phone_patterns)
ruler.add_patterns(date_patterns)

# Load Hugging face model
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
nlp_hugging_face = pipeline("ner", model=model, tokenizer=tokenizer)


def recognize_entity(nlp_model, text):
    # Recognizes and extracts entities from the given text using an NLP model
    return nlp_model(text)


def replace_with_black_block_by_indices(text, start, end):
    # Calculate the length of the substring to be replaced
    length = end - start

    # Replace the substring with black blocks
    censored_text = text[:start] + ('█' * length) + text[end:]
    return censored_text


def censor_with_spacy(text, entities_to_censor, stats):
    # Process the text with SpaCy
    doc = recognize_entity(nlp_spacy, text)

    # Censor required entities from the entity pool
    censored_text = text
    for ent in doc.ents:
        ent_label = ent.label_
        entity_text = ent.text
        if ent_label in entities_to_censor:
            censored_text = censored_text.replace(entity_text, '█' * len(entity_text))

            # Update stats for output
            ent_start_char = ent.start_char
            ent_end_char = ent.end_char
            if ent_label in stats:
                stats[ent_label]['count'] += 1
                stats[ent_label]['indices'].append((ent_start_char, ent_end_char))
            else:
                stats[ent_label] = {'count': 1, 'indices': [(ent_start_char, ent_end_char)]}

    return censored_text


def censor_with_hf(text, entities_to_censor, stats):
    # Process the text with Hugging face
    doc = recognize_entity(nlp_hugging_face, text)

    # Convert text to list of characters
    censored_text_list = list(text)

    for ner in doc:
        entity_type = ner['entity']
        if entity_type in entities_to_censor:
            # Update the count in stats using dict.get for cleaner code
            stats[entity_type] = stats.get(entity_type, 0) + 1

            start_idx, end_idx = ner['start'], ner['end']
            # Replace the entire entity with blocks in one operation
            censored_text_list[start_idx:end_idx] = '█' * (end_idx - start_idx)

            # # Replace characters within the entity with blocks
            # i = start_idx
            # while censored_text_list[i].isalpha():
            #     censored_text_list[i] = '█'
            #     i += 1

        # Join the list back into a string and return
    return ''.join(censored_text_list)


def check_entity_regex(text, entity):
    if entity == 'NAME':
        ent_regex = (r"\b(?:(?:[A-Z][a-z]+,?\s)?[A-Z][a-z]*\.?(?:\s|\s?[A-Z][-])?[A-Z]?[a-z]*\.?|[A-Z][a-z]+(?:[-']["
                     r"A-Z][a-z]+)?(?:\s[A-Z]\.?\s?[A-Z]?[a-z]*\.?)?)\b")
    else:
        return []

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


def censor_with_regex(text, entities_to_censor):
    censored_text = text
    if 'PERSON' in entities_to_censor:
        name_regex_list = check_entity_regex(text, 'NAME')
        for ent in name_regex_list:
            # Parse with Spacy
            parsed_word = recognize_entity(nlp_spacy, ent[0])
            for par_ent in parsed_word.ents:
                en_label = par_ent.label_
                if en_label in entities_to_censor:
                    censored_text = censored_text.replace(par_ent.text, '█' * len(par_ent.text))

    return censored_text


def write_censored_file(censored_text, output_file_path):
    # Write the censored text to a new file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        print("aaaa: ", output_file_path)
        file.write(censored_text)

