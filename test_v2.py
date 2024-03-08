import spacy

nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

# Define patterns for typical US phone number formats
phone_patterns = [
    {"label": "PHONE", "pattern": [{"SHAPE": "ddd"}, {"ORTH": "-"}, {"SHAPE": "ddd"}, {"ORTH": "-"}, {"SHAPE": "dddd"}]},
    {"label": "PHONE", "pattern": [{"SHAPE": "(ddd)"}, {"ORTH": " "}, {"SHAPE": "ddd"}, {"ORTH": "-"}, {"SHAPE": "dddd"}]},
    {"label": "PHONE", "pattern": [{"SHAPE": "ddd"}, {"ORTH": "."}, {"SHAPE": "ddd"}, {"ORTH": "."}, {"SHAPE": "dddd"}]},
]

ruler.add_patterns(phone_patterns)

text = "Call me at 415-555-1234 or (415) 555-1234 or 415.555.1234."
doc = nlp(text)

# Create a list to gather all entities first
redactions = [(ent.text) for ent in doc.ents if ent.label_ == "PHONE"]

# Replace each entity found with "[REDACTED]"
for number in redactions:
    text = text.replace(number, "[REDACTED]")

print(text)
