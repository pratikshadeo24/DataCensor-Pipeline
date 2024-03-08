import re
import spacy
from snorkel.labeling import labeling_function, PandasLFApplier
from snorkel.labeling.model import LabelModel
import pandas as pd

# Load SpaCy for basic NER tasks (names and dates)
nlp = spacy.load("en_core_web_lg")

# Define some simple labeling functions
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

# Load your data
# Assuming you have a DataFrame 'df' with a column 'text' containing your data
# For demonstration, let's create a dummy DataFrame:
df = pd.DataFrame({"text": ["Call me at 415-555-1234.", "Call me at (123) 456-7890", "Call me at +1 123-456-7890", "Call me at 123 456 7890", "Meet me at 123 Main St.", "John Doe's birthday is 01/01/2000."]})

# Apply the labeling functions
lfs = [lf_contains_phone_number, lf_contains_address, lf_contains_name, lf_contains_date]
applier = PandasLFApplier(lfs=lfs)
L_train = applier.apply(df=df)

# Train the label model
label_model = LabelModel(cardinality=2, verbose=True)
label_model.fit(L_train, n_epochs=500, log_freq=100, seed=123)

# Predict the labels
df["label"] = label_model.predict(L=L_train, tie_break_policy="abstain")

# Now you would use the predicted labels to censor information
# For simplicity, let's just print out the censored texts:
for index, row in df.iterrows():
    print(f"Original: {row['text']}")
    if row['label'] == 1:
        # Just a simple placeholder for actual censorship logic
        print("Censored: [REDACTED]")
    else:
        print("Censored: No sensitive information found.")
