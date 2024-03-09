# CIS6930SP24 - Assignment1

#### Name: Pratiksha Deodhar

## Description
The objective of this project is to design and implement a data pipeline that is proficient in detecting and censoring sensitive information within the Enron email dataset. This entails developing a system that can meticulously iterate through all email files identified by a specified glob pattern. Upon identification, the system applies its censorship logic to redact sensitive content found within each email. Following the redaction process, the pipeline is responsible for securely storing these censored emails in a designated folder. This ensures not only the secure handling of sensitive data but also organizes the output in a manner that facilitates easy archiving and accessibility for subsequent review or utilization.

## How to Install
### 1. Download pyenv:
```commandline
$ curl https://pyenv.run | bash
```
### 2. Install Python 3.11:
```commandline
$ pyenv install 3.11
```
### 3. Set it globally:
```commandline
$ pyenv global 3.11
```

### 4. Install required libraries
```commandline
$ pipenv install pypdf 
$ pipenv install sqlite3
$ pipenv install pytest
$ pipenv install pytest-mock
```

## How to Run
```commandline
$ pipenv run python censoror.py --input <input_file_path> --names --dates --phones --address --output <output_file_path> --stats stderr
```

## Demo
[DE_Compressed_video.mov](..%2F..%2FDE_Compressed_video.mov)

## Code Description

### main
This function orchestrates the censorship process on a collection of text files, targeting specified types of sensitive information. It accepts four arguments. The function processes each matched file by censoring the designated information and saving the redacted content to the output directory. The function does not return a value but produces censored files and optionally outputs statistics regarding the redaction 

Function arguments:
- input_pattern (string): Glob pattern to identify input files.
- output_dir (string): Directory to save redacted files.
- entities_to_censor (list): List of entity types to redact.
- stats_output : Channel to output processing statistics.

Return value: None. (Redacted text files saved in the specified output directory and optional stats displayed in the chosen output channel)

### censor_spacy
This function is responsible for identifying and censoring specific entities in a given text using the SpaCy NLP library. The function processes the text with SpaCy, identifies entities matching those listed in entities_to_censor, and replaces them with a series of black block characters ('█') equal in length to the entity being censored. It then returns the modified text with these entities redacted, maintaining the original text structure and content, minus the sensitive information.

Function arguments: 
- text (string) : the input text to be processed 
- entities_to_censor (list) : a list of entity types designated for redaction

Return value: 
- censored_text (string) : modified text with these entities redacted

### censor_hf
The censor_hf function is designed to detect and redact specific types of entities within a text, leveraging a model from the Hugging Face Transformers library. The function first processes the text using a named entity recognition pipeline from Hugging Face to identify pertinent entities. Then, it iteratively replaces each identified entity that matches the types listed in entities_to_censor with a series of black block characters ('█'), ensuring the length of the replacement matches the original entity length.

Function arguments: 
- text (string) : string content to be processed.
- entities_to_censor (list) : a list specifying which entity types should be obscured

Return value: 
- censored_text (string) : censored version of the text, where all specified entities have been effectively masked

### extract_incidents
This function is designed to process binary data of a PDF document, extract text content from each page, and then 
compile the text into a structured format, presumably a list of incidents.
- Function arguments: incident data from `fetch_incidents` function
- Return value: list of incidents

### extract_page_text
This function is designed to extract text in the form of list of strings where each string represents a line of text 
extracted from the current page, with special considerations for the first and last pages of the document.
- Function arguments: 
  - page (PageObject)
  - page_num (int)
  - tot_pages (int)
- Return value: split_incidents (list of strings)

### split_all_incidents
This function is designed to process a block of text (page_text) and extract individual incidents from it
- Function arguments:
  - page_text: entire page content (list)
- Return value: incidents of particular page (list)

### refactor_page_data
This function processes a list of strings, each representing a line of text extracted from a PDF page, and transforms
this text to get data of incident's time, number, location, nature, ORI.
- Function arguments: page_text, (list of strings)
- Return value: page_incidents, (list of dictionaries) with all incident arguments

### extract_location_and_nature
This function is designed to parse a segment of text and separate it into two components: the location and the nature 
of an incident. This parsing is based on certain conditions related to the content and its format.
- Function arguments: record, which is a segment of individual record list
- Return value: 
  - loc_str: incident location (string)
  - nature_str: incident nature (string)

### create_db
This function is designed to create a new SQLite database and create a table within it for storing incident data.
- Function arguments: db_name (string)
- Return value: conn (database connection object)

### populate_db
This function is designed to insert a collection of incident records into incidents table in the created database
- Function arguments: db (database connection object)
- Return value: None

### status
This function is designed to query an SQLite database to group incident records by their nature, count the number of 
occurrences of each distinct nature, and then print out the records in order by count DESC and nature ASC.
- Function arguments: db (database connection object)
- Return value: None

## Database Development
Execution of code checks if the database exists. If it exists, it first removes the database and then create a new
database "norman_pd.db" within resources directory. It also creates a table "incidents" within
the database which has the following columns - Incident Time, Incident Number, Location, Nature, Incident ORI.
Incidents are collected and then populated into the database in one go. 

## Tests
- The test use pytest fixtures to provide a fixed baseline upon which tests can reliably and repeatedly execute. Examples include mock_cwd to mock the current working directory, sample_url for providing a sample URL etc.
- The tests use the mocker fixture to patch Python's standard modules like os and urllib to mock their behavior for the tests.
- Several tests (test_delete_existing_db_file_exists, test_create_db_success, etc.) are designed to check the database-related functions.
- Other tests (test_fetch_incidents_success, test_extract_incidents, etc.) are meant to verify that the code can fetch data from a URL, read PDF content, extract text, and parse it into a structured format.
- After each action, the tests make assertions to verify that the expected results are obtained. This includes checking return values, making sure functions are called with the correct arguments, and ensuring no side effects occur in case of errors.

## Bugs and Assumptions
- Program will treat and redact all entities as - 
  - name where _ent.label in ['PERSON', 'B-PER', 'I-PER']
  - address where _ent.label in ['ADDRESS', 'B-LOC', 'I-LOC', 'GPE', 'FAC', 'LOC']
  - date where _ent.label = 'DATE'
  - phone where _ent.label = 'PHONE'
- Program was tested with all the spacy models(`en_core_web_sm`, `en_core_web_md`, `en_core_web_lg`, `en_core_web_trf`) but results were better with `en_core_web_md`
- Code was tested with different models(`dslim/bert-base-NER`, `dbmdz/bert-large-cased-finetuned-conll03-english`) of hugging face but the results were better with `dslim/bert-base-NER`
- Spacy date labels are extended by adding patterns using entity ruler. So the following date patterns in addition to spacy's default ones can be redacted- 
  - 14 May 2001
  - 05/03/2001
  - April 18, 2001
  - Dec. 15
  - 12/13/2000
  - February 12
  - 10/11/01
  - 13/05/2001
  - 12.02.2001
  - Jan 18, 2001
- Spacy phone labels are extended by adding patterns using entity ruler. So the following phone patterns in addition to spacy's default ones can be redacted-
  - 123-456-7890
  - (123) 456-7890
  - +1 123-456-7890
  - 1-123-456-7890
  - 123.456.7890
  - 123 456 7890
  - 512)263-0177
- Spacy and hugging face are giving better performance for dates and phone numbers but somewhat poor performance while redacting names and addresses because of the varying format in which they exist in the dataset.
- Program does not work efficiently when any of the models is used in single, but they work comparatively better when used in combination. Meaning passing the text from spacy first and then through hugging face.
