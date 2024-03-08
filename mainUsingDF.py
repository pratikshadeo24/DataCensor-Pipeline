import argparse
import glob
import os
import spacy
import re
import numpy as np
from snorkel.labeling import labeling_function, PandasLFApplier, LFAnalysis
from snorkel.labeling.model import LabelModel
import pandas as pd

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

def load_data(pattern):
    files = glob.glob(pattern)
    texts = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            texts.append(f.read())
    return texts

# Define a helper function that checks individual entities
# def check_entity_label(entities, target_label):
#     return any(entity.label_ == target_label for entity in entities)

# Define labeling functions
@labeling_function()
def lf_contains_phone_number(x):
    # Simple regex for US phone numbers
    doc = nlp(x.text)
    has_phone_indicators = bool(ent.label_ == 'PHONE' for ent in doc.ents)
    has_phone_number = bool(re.search(r"(?:\+1\s*(?:[.-]\s*)?)?(?:\(\s*(\d{3})\s*\)|(\d{3}))[\s.-]?(\d{3})[\s.-]?(\d{4})(?:\s*(?:ext\.?|x)\s*(\d{2,5}))?", x.text))
    return 1 if has_phone_indicators or has_phone_number else 0

@labeling_function()
def lf_contains_address(x):
    # Enhanced address detection using common address components
    has_address_indicators = bool(re.search(r'\b(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b', x.text))
    has_numerics = bool(re.search(r'\b\d{1,6}\b', x.text))  # Looking for street numbers
    doc = nlp(x.text)
    address_related_entities = ['GPE', 'ORG', 'FAC', 'LOC']
    has_gpe = any(ent.label_ in address_related_entities for ent in doc.ents)
    return 1 if has_address_indicators or has_numerics or has_gpe else 0

@labeling_function()
def lf_contains_name(x):
    # Leverage SpaCy's NER for name detection
    doc = nlp(x.text)
    return 1 if any(ent.label_ == "PERSON" for ent in doc.ents) else 0

@labeling_function()
def lf_contains_date(x):
    # Leverage SpaCy's NER for date detection
    has_date_indicators = bool(re.search(r'(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})', x.text))
    doc = nlp(x.text)
    has_date = any(ent.label_ == "DATE" for ent in doc.ents)
    return 1 if has_date_indicators or has_date else 0


# You would define more labeling functions based on your requirements

def apply_labeling_functions(texts, args):
    # Create a DataFrame to hold text data for Snorkel processing
    df = pd.DataFrame({'text': texts})

    # Apply SpaCy model to each text to extract entities
    df['ents'] = df['text'].apply(lambda txt: list(nlp(txt).ents))

    # Flatten out entity labels for Snorkel
    df_exploded = df.explode('ents')

    lfs = []
    if args.names:
        lfs.append(lf_contains_name)
    if args.dates:
        lfs.append(lf_contains_date)
    if args.phones:
        lfs.append(lf_contains_phone_number)
    if args.address:
        lfs.append(lf_contains_address)

    if not lfs:
        raise ValueError("No entities selected for censorship.")

    applier = PandasLFApplier(lfs=lfs)
    L_train = applier.apply(df=df_exploded)

    return L_train, df_exploded


def aggregate_labels(L_train):
    label_model = LabelModel(cardinality=2, verbose=True)
    label_model.fit(L_train, n_epochs=100, log_freq=50, seed=123)
    return label_model


def censor_data(texts, df_exploded, label_model, L_train):
    censored_texts = []

    # Get the predictions
    df_exploded['pred'] = label_model.predict(L=L_train)

    # Iterate over texts and censor based on predictions
    for i, text in enumerate(texts):
        entities = df_exploded[df_exploded.index.get_level_values(0) == i]
        censored_text = text
        for _, row in entities.iterrows():
            if row['pred'] == 1:
                censored_text = censored_text.replace(row['ents'].text, '*' * len(row['ents'].text))
        censored_texts.append(censored_text)

    return censored_texts


def save_data(texts, output_dir):
    for i, text in enumerate(texts):
        with open(os.path.join(output_dir, f'{i}.censored.txt'), 'w', encoding='utf-8') as f:
            f.write(text)


def main(args):
    texts = load_data(args.input)
    L_train, df_exploded = apply_labeling_functions(texts, args)
    label_model = aggregate_labels(L_train)
    censored_texts = censor_data(texts, df_exploded, label_model, L_train)
    save_data(censored_texts, args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Glob pattern for input files')
    parser.add_argument('--output', type=str, required=True, help='Output directory for censored files')
    parser.add_argument('--names', action='store_true', help='Flag to censor names.')
    parser.add_argument('--dates', action='store_true', help='Flag to censor dates.')
    parser.add_argument('--phones', action='store_true', help='Flag to censor phone numbers.')
    parser.add_argument('--address', action='store_true', help='Flag to censor addresses.')
    args = parser.parse_args()
    main(args)
