import argparse
import glob
import os
import spacy
import numpy as np
# from snorkel.labeling import
from snorkel.labeling.model import LabelModel
# from snorkel.preprocess.Preprocessor import preprocess_text

def load_data(pattern):
    files = glob.glob(pattern)
    texts = []
    for file in files:
        with open(file, 'r') as f:
            texts.append(f.read())
    return texts

# def preprocess(texts):
#     preprocessed_texts = []
#     for text in texts:
#         preprocessed_texts.append(preprocess_text(text))
#     return preprocessed_texts

def preprocess(texts):
    nlp = spacy.load('en_core_web_sm')
    preprocessed_texts = []
    for text in texts:
        doc = nlp(text)
        # Joining tokenized text and removing newline and extra spaces
        processed_text = ' '.join([token.text for token in doc]).replace('\n', ' ').replace('  ', ' ')
        preprocessed_texts.append(processed_text)
    return preprocessed_texts

def label_data(nlp, texts, entities_to_censor):
    labels = []
    for text in texts:
        doc = nlp(text)
        label = []
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and ent.label_ in entities_to_censor:
                label.append((ent.start_char, ent.end_char, 'PERSON'))
            elif ent.label_ == 'DATE' and ent.label_ in entities_to_censor:
                label.append((ent.start_char, ent.end_char, 'DATE'))
            elif ent.label_ == 'PHONE' and ent.label_ in entities_to_censor:
                label.append((ent.start_char, ent.end_char, 'PHONE'))
            elif ent.label_ == 'CARDINAL' and ent.label_ in entities_to_censor:
                label.append((ent.start_char, ent.end_char, 'ADDRESS'))
        labels.append(label)
    return labels

def train_label_model(L_train, n_epochs=50):
    lm = LabelModel(cardinality=3, verbose=True)
    lm.fit(L_train, n_epochs=n_epochs, lr=0.001)
    return lm

def censor_data(texts, labels, lm):
    censored_texts = []
    for text, label in zip(texts, labels):
        censored_text = text
        for start, end, category in label:
            if lm.predict([start, end, category]) == 1:
                censored_text = censored_text[:start] + '*' * (end - start) + censored_text[end:]
        censored_texts.append(censored_text)
    return censored_texts

def save_data(texts, output_dir):
    for i, text in enumerate(texts):
        with open(os.path.join(output_dir, f'{i}.censored'), 'w') as f:
            f.write(text)

def main(args):

    CENSOR_ENTITIES = []
    if args.names:
        CENSOR_ENTITIES.append('PERSON')
    if args.dates:
        CENSOR_ENTITIES.append('DATE')
    if args.phones:
        # Note: Implement custom logic for phone number recognition
        CENSOR_ENTITIES.append('PHONE')
    if args.address:
        # Note: Implement custom logic for address recognition
        CENSOR_ENTITIES.append('ADDRESS')

    texts = load_data(args.input)
    preprocessed_texts = preprocess(texts)
    nlp = spacy.load('en_core_web_sm')
    labels = label_data(nlp, preprocessed_texts, CENSOR_ENTITIES)
    L_train = [(preprocessed_text, label) for preprocessed_text, label in zip(preprocessed_texts, labels)]
    # L_train = np.array(labels, dtype=int)
    lm = train_label_model(L_train)
    censored_texts = censor_data(texts, labels, lm)
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