# OpenRouter LLM NER Tester

This repository contains a set of Python scripts designed to interact with Large Language Models (LLMs) available through OpenRouter. The scripts are capable of retrieving the available LLM models, deduplicating the list to ensure only the most recent versions are present, and testing them for Named Entity Recognition (NER) capabilities using a chapter from a book.

## Contents

- `fetch.py`: This script is responsible for fetching the list of available LLM models from OpenRouter.
- `main.py`: The main driver script that utilizes functions from `common_functions.py` to deduplicate the models list and test NER capabilities.
- `common_functions.py`: Contains shared functions used by other scripts, such as deduplication logic and NER testing functions.

## Getting Started

### Prerequisites

- Python 3.8 or higher.
- An API key from OpenRouter. See the section below on how to set this up.

### API Key Configuration

To use this project, you need to obtain an API key from OpenRouter. Once you have it, you should set it as an environment variable called OPENROUTER_API_KEY on your system:

### Installation

1. Clone the repository to your local machine.
2. Navigate to the cloned directory.

### Usage

1. Place a text file named `chapter.txt` containing the chapter you want to test in the root directory of the project.
2. Run the `main.py` script to start the process:

The script will automatically:
- Fetch the latest LLM models from OpenRouter.
- Deduplicate the models to retain only the latest versions.
- Test each model's NER capabilities using the content of `chapter.txt`.

### Output

The results of the NER tests will be saved as a JSON file

## TODO
- Adjust chunking based on context window size allowed by each model
- Fix Google chunking

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
