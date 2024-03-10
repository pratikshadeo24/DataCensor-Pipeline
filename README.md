# CIS6930SP24 - Assignment1

#### Name: Pratiksha Deodhar

## Description
<p align="justify"> The objective of this project is to design and implement a data pipeline that is proficient in detecting and censoring sensitive information within the Enron email dataset. This entails developing a system that can meticulously iterate through all email files identified by a specified glob pattern. Upon identification, the system applies its censorship logic to redact sensitive content found within each email. Following the redaction process, the pipeline is responsible for securely storing these censored emails in a designated folder. This ensures not only the secure handling of sensitive data but also organizes the output in a manner that facilitates easy archiving and accessibility for subsequent review or utilization. </p>

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
$ pipenv install spacy 
$ pipenv install torchvision
$ pipenv install transformers
$ pipenv install $(spacy info en_core_web_md --url)
$ pipenv install pytest
$ pipenv install pytest-mock
```

## How to Run code
```commandline
$ pipenv run python censoror.py --input <input_file_path> --names --dates --phones --address --output <output_file_path> --stats <stderr or stdout or specific file path>
```

## How to Run Pytest
```commandline
$  pipenv run python -m pytest
```

## Demo
https://github.com/pratikshadeo24/cis6930sp24-assignment1/assets/30438714/be96e223-7659-442b-96d3-6f8efc1f9ab6

## Function Description

### main
<p align="justify"> This function orchestrates the censorship process on a collection of text files, targeting specified types of sensitive information. It accepts four arguments. The function processes each matched file by applying different models in sequence - space, hugging face and then regex  and saving the redacted content to the output directory. The function does not return a value but produces censored files and optionally outputs statistics regarding the redaction. </p>

Function arguments:
- input_pattern (string): Glob pattern to identify input files.
- output_dir (string): Directory to save redacted files.
- entities_to_censor (list): List of entity types to redact.
- stats_output : Channel to output processing statistics.

 <p align="justify"> Return value: None. (Redacted text files saved in the specified output directory and optional stats displayed in the chosen output channel). </p>

### censor_with_spacy
<p align="justify"> This function is responsible for identifying and censoring specific entities in a given text using the SpaCy NLP library. The function processes the text with SpaCy, identifies entities matching those listed in entities_to_censor, and replaces them with a series of black block characters ('█') equal in length to the entity being censored. It then returns the modified text with these entities redacted, maintaining the original text structure and content, minus the sensitive information. </p>

Function arguments: 
- text (string) : the input text to be processed 
- entities_to_censor (list) : a list specifying which entity types should be redacted
- stats (dictionary) : dictionary containing collected stats

Return value: 
- censored_text (string) : modified text with these entities redacted

### censor_with_hf
<p align="justify"> The censor_hf function is designed to detect and redact specific types of entities within a text, leveraging a model from the Hugging Face Transformers library. The function first processes the text using a named entity recognition pipeline from Hugging Face to identify pertinent entities. Then, it iteratively replaces each identified entity that matches the types listed in entities_to_censor with a series of black block characters ('█'), ensuring the length of the replacement matches the original entity length. </p>

Function arguments: 
- text (string) : text to be processed.
- entities_to_censor (list) : a list specifying which entity types should be redacted
- stats (dictionary) : dictionary containing collected stats

Return value: 
- censored_text (string) : censored version of the text, where all specified entities have been effectively masked


### censor_with_regex
<p align="justify"> This function is designed to identify and redact specific types of sensitive information from a given text using regular expressions. In this context, it specifically targets and censors named entities that are recognized as persons. The function employs a regular expression pattern to find potential person names within the text and then uses the SpaCy NLP library to confirm these entities before redacting them. The redaction process involves replacing each identified entity with a series of black blocks (█) of equal length to the censored entity, thus masking the original text while maintaining its structure. </p>

Function arguments: 
- text (string) : text that needs to be processed and censored
- entities_to_censor (list) : a list specifying which entity types should be redacted

Return value:
- censored_text (string) : censored version of the text, where name entities have been effectively masked

### recognize_entity
<p align="justify"> This function serves as an entity recognition utility that leverages a given Natural Language Processing (NLP) model to detect and extract entities from the provided text. </p>

Function arguments: 
- nlp_model (model object): NLP model that the function utilizes
- text (string) : text to be processed by the NLP model

<p align="justify"> Return value (Doc or list): If SpaCy is the underlying technology, the function returns a Doc object enriched with entity annotations. For a Hugging Face model, it typically returns a list of dictionaries, each representing an identified entity with details like the entity type, text, and character indices in the input text. </p>


### replace_with_black_block_by_indices
<p align="justify"> The function is specifically used by censor_with_regex function  to censor parts of a text by replacing specified sections with a series of black blocks (█). It targets the portion of the text defined by the starting and ending indices and replaces that substring with a sequence of black blocks of equivalent length. </p>

Function arguments:
- text (string) : text to be censored
- start (int) :  starting index of the segment within the text that needs to be redacted
- end (int) : ending index of the segment within the text to be censored

Return Value: 
- censored_text (string) : resulting string after the specified segment has been censored

### check_entity_regex
<p align="justify"> This function is designed to identify entities in a given text based on regular expression patterns. Right now, it targets only the potential name entities within the text, applies a regular expression to find matches that correspond to specific entity types, and returns these findings along with their positions. </p>

Function arguments: 
- text (string) : text to be scanned for potential entities
- entity (string) : specifier that determines the type of entity the function should look for

Return value: 
- output (list of tuples) : function returns a list of tuples, where each tuple corresponds to a detected entity

### write_censored_file
This function takes censored text and writes it to a specified output file. 

Function arguments:
- censored_text (string) : string containing the text after the sensitive information has been redacted
- output_file_path (string or Path) : file path where the censored text will be saved

Return value: 
- None. Output is the creation of a new file at the specified path

### output_stats
<p align="justify">This function is designed to compile and display statistical data regarding the censorship process applied to a text file. Specifically, it summarizes the count of each entity type that was censored within the document.</p>

Function arguments:
- stats (dict) : dictionary contains the counts of each entity type that has been censored
- stats_output (string) : parameter specifies the destination for the output statistics 
- censored_file_path (Path or string) : path to the censored file

Return value: 
- None. outputs the statistics message either to the console (via stderr or stdout) or to a specified file

### extract_arguments
<p align="justify"> This function interprets and organizes the command-line arguments provided to the censorship script </p>

Function arguments:
- arg_parser (Namespace) : object returned by argparse after parsing the command-line arguments

Return value: 
- inp_path (string) : path to the input file or directory containing the text files to be censored
- out_path (string): path to the output directory where the censored files will be saved
- out_stats (string) : output destination for the statistics regarding the redaction process
- entities_to_censor (list) : list of entity types that the script will target for censorship

### arguments_parser
<p align="justify">This function is designed to define and parse the command-line arguments </p>

Function arguments:
- None

Return value: 
- argparse.Namespace object

## Tests
### test_censoror.py:

Fixtures:
- mock_read_text: Mocks Path.read_text to simulate reading files without accessing the file system.
- mock_glob: Mocks the glob function to return a predefined list of file paths, emulating file discovery in a directory.
- mock_write_censored_file: Mocks the write_censored_file function to verify its invocation without actually writing files.
- mock_censor_functions: Mocks the various censoring functions (censor_with_spacy, censor_with_hf, censor_with_regex) and output_stats to check their integration within the main workflow.

Test Functions:
- test_main_empty_input: Verifies that no action is taken when an empty input pattern is provided.
- test_main: Checks that the main function processes files correctly using mocked paths and censoring functions, asserting proper calls to read, process, and write operations.
- test_main_stderr_output: Ensures that the main function correctly handles and routes output when configured to print stats to stderr.

### test_main.py:

Fixtures:
- Several fixtures mock the behavior of NLP models (mock_recognize_entity, mock_nlp_hugging_face, mock_spacy_doc) to provide controlled responses for entity recognition.

Test Functions:
- Functions like test_recognize_entity_spacy and test_recognize_entity_huggingface validate the entity recognition process using different NLP tools.
- test_replace_with_black_block_by_indices checks the functionality of replacing identified sensitive text with censorship blocks.
- Various tests (test_censor_with_spacy_correct_entities, test_censor_with_hf_entities, etc.) examine the behavior of censorship functions under different conditions, confirming that they correctly censor identified entities and leave uncensored entities untouched.

### test_utils.py:

Fixtures:
- mock_arg_parser: Creates a mock argument parser object to simulate different command-line arguments scenarios.

Test Functions:
- test_output_stats_to_stderr and test_output_stats_to_stdout verify that stats are correctly output to the designated streams.
- test_output_stats_to_file checks if stats are properly written to a file when specified.
- Tests like test_extract_arguments_all_arg_passed and test_extract_arguments_no_arg_passed assess the argument extraction logic, ensuring it correctly interprets various combinations of command-line arguments.
- test_parse_arguments_with_all_options and test_parse_arguments_with_minimum_required_options validate the argument parsing functionality, ensuring all necessary options are correctly captured and defaults are applied appropriately.

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
  - +1 123-456-7890 (Pattern does not properly redact +1)
  - 1-123-456-7890 (Pattern does not properly redact starting 1)
  - 123.456.7890 (Pattern is not working for these formats)
  - 123 456 7890
  - 512)263-0177
- Spacy and hugging face are giving better performance for dates and phone numbers but somewhat poor performance while redacting names and addresses because of the varying format in which they exist in the dataset.
- Program does not work efficiently when any of the models is used in single, but they work comparatively better when used in combination. Meaning passing the text from spacy first and then through hugging face.
