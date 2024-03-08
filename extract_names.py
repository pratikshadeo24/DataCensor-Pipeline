import csv
import random

# Replace 'yourfile.csv' with the path to your CSV file
file_path = 'datasets/babynames1880-2020.csv'

TRAIN_DATA = [
    # Email addresses with first name and last name
    ("john.doe@example.com", [(0, 8, "PERSON")]),
    ("jane.roe@example.com", [(0, 8, "PERSON")]),

    # Email addresses with initials and last name
    ("j.doe@example.com", [(0, 5, "PERSON")]),
    ("a.smith@example.com", [(0, 7, "PERSON")]),

    # Email addresses with first name, middle initial, and last name
    ("john.q.public@example.com", [(0, 13, "PERSON")]),
    ("jane.a.roe@example.com", [(0, 10, "PERSON")]),

    # Email addresses with underscores or hyphens
    ("john_doe@example.com", [(0, 8, "PERSON")]),
    ("jane-doe@example.com", [(0, 8, "PERSON")]),

    # Other common patterns
    ("bob@example.com", [(0, 3, "PERSON")]),
    ("alice@example.com", [(0, 5, "PERSON")])

]

# ("{person_name_1} and {person_name_2} are attending the meeting today.",
#      {"entities": [(0, 8, "PERSON"), (13, 21, "PERSON")]}),

sentence_list = [{"{person_name} decided to take a walk in the park.": (0, "{name_len}", "PERSON")},
                 {"The gift was chosen carefully by {person_name}.": (33, "{name_len}", "PERSON")},
                 {"In the library, {person_name} found a rare book.": (16, "{name_len}", "PERSON")},
                 {"Can you ask {person_name} if he has finished his homework?": (12, "{name_len}", "PERSON")},
                 {"The song sung by {person_name} was very touching.": (17, "{name_len}", "PERSON")},
                 {"At the meeting, {person_name} presented a brilliant idea.": (16, "{name_len}", "PERSON")},
                 {"{person_name}'s artwork was displayed at the gallery.": (0, "{name_len}", "PERSON")},
                 {"The joke told by {person_name} made everyone laugh.": (17, "{name_len}", "PERSON")},
                 {"In the morning, {person_name} likes to meditate.": (16, "{name_len}", "PERSON")},
                 {"The letter written by {person_name} was heartfelt.": (22, "{name_len}", "PERSON")},
                 {"During the tour, {person_name} learned a lot about the city's history.": (17, "{name_len}", "PERSON")},
                 {"The recipe from {person_name} turned out to be fantastic.": (16, "{name_len}", "PERSON")},
                 {"At the reunion, {person_name} was the center of attention.": (16, "{name_len}", "PERSON")},
                 {"The garden maintained by {person_name} is beautiful.": (25, "{name_len}", "PERSON")},
                 {"In the competition, {person_name} won the first prize.": (20, "{name_len}", "PERSON")},
                 {"The story told by {person_name} was fascinating.": (18, "{name_len}", "PERSON")},
                 {"On the trip, {person_name} took many stunning photos.": (13, "{name_len}", "PERSON")},
                 {"The speech delivered by {person_name} was powerful.": (24, "{name_len}", "PERSON")},
                 {"The cake baked by {person_name} was delicious.": (18, "{name_len}", "PERSON")},
                 {"In the play, {person_name} played the lead role.": (13, "{name_len}", "PERSON")},
                 {"The advice given by {person_name} was very useful.": (20, "{name_len}", "PERSON")},
                 {"At the workshop, {person_name} learned new skills.": (17, "{name_len}", "PERSON")},
                 {"The poem written by {person_name} was moving.": (20, "{name_len}", "PERSON")},
                 {"During the game, {person_name} scored the winning goal.": (17, "{name_len}", "PERSON")},
                 {"The project headed by {person_name} was a success.": (22, "{name_len}", "PERSON")},
                 {"In the choir, {person_name}'s voice was remarkable.": (14, "{name_len}", "PERSON")},
                 {"The dress designed by {person_name} was stunning.": (22, "{name_len}", "PERSON")},
                 {"At the party, {person_name}'s costume was the most creative.": (14, "{name_len}", "PERSON")},
                 {"The book authored by {person_name} received great reviews.": (21, "{name_len}", "PERSON")},
                 {"In the class, {person_name} answered the question correctly.": (14, "{name_len}", "PERSON")},
                 {"{person_name}_Dec2000": (0, "{name_len}", "PERSON")},
                 {"{person_name}\'Sent Mail": (0, "{name_len}", "PERSON")}]

# Initialize an empty list to store the second column values
second_column_values = []

# Open the CSV file and read it
with open(file_path, mode='r') as csv_file:
    # Create a CSV reader object
    csv_reader = csv.reader(csv_file)

    # Skip the header row if your CSV file has one
    next(csv_reader)

    # Iterate over each row in the CSV file
    for row in csv_reader:
        # Check if the row has at least two columns
        if len(row) >= 2:
            # Append the value from the second column to the list
            second_column_values.append((row[1], [(0, len(row[1]), "PERSON")]))
            train_case = random.choice(sentence_list)
            for k, v in train_case.items():
                h = (v[0], (v[0]+len(row[1])), v[-1])
                second_column_values.append((k.replace("{person_name}", row[1]), [h]))

# At this point, second_column_values contains all the values from the second column
second_column_values.extend(TRAIN_DATA)
second_column_values.append(("Allen, Phillip K.\'Sent Mail", [(0, 5, "PERSON"), (7, 17, "PERSON")]))

with open('train_data.txt', 'w') as f:
    f.write(str(second_column_values))

