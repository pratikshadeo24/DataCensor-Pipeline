import spacy
import ast
from spacy.tokens import DocBin

nlp = spacy.load('en_core_web_sm')
training_data = "training_data.txt"
dev_data = "dev_data.txt"


def compute(model_data, data_ty):
    with open(model_data, mode='r') as file:
        content = file.read()
        train_data = ast.literal_eval(content)
        # the DocBin will store the example documents
        db = DocBin()
        for text, annotations in train_data:
            doc = nlp(text)
            ents = []
            for start, end, label in annotations:
                span = doc.char_span(start, end, label=label)
                ents.append(span)
            ents = [span for span in ents if span is not None]  # Filter out None to avoid errors.
            if ents:  # Only set doc.ents if there are valid entities.
                doc.ents = ents
            doc.ents = ents
            db.add(doc)

    db.to_disk(f"./{data_ty}.spacy")


compute(training_data, "trained")
compute(dev_data, "dev")

