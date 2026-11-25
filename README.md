
# Entity Extraction & Matching from PDFs using GenAI

## Project Overview

This project extracts important entities from two PDF documents using Generative AI and NLP techniques. It identifies relevant information and compares the extracted entities to find matching and similar values.

The sample use case involves comparing an OBOL document with a Sea Waybill document.

## Features

- Extract text from PDF documents.
- Extract entities using Google Gemini API.
- Identify named entities using Hugging Face BERT-based NER.
- Extract booking numbers, vessel names, dates, addresses and shipping references.
- Compare entities across two PDF documents.
- Identify exact matches and similar candidates.
- Generate Excel reports containing extraction and comparison results.
- Provide a Streamlit interface for uploading and processing PDFs.

## Technologies Used

- Python
- Google Gemini API
- Hugging Face Transformers
- BERT Named Entity Recognition
- LangChain
- PyPDF
- Pandas
- OpenPyXL
- Streamlit

## Project Architecture

1. Upload two PDF documents.
2. Extract PDF text using LangChain PyPDFLoader.
3. Send document text to Gemini for entity extraction.
4. Apply Hugging Face BERT NER for general named entity recognition.
5. Normalize and compare extracted entity values.
6. Identify exact matches, similar candidates and unmatched values.
7. Export the results into Excel.

## Default Entity Fields

### PDF 1 - OBOL Document

- Booking No
- Address
- Order No
- Vessel name
- OBOL number
- Depart date
- Cutoff date
- Destination port
- Total ROLL Shipped
- Total Lots Shipped
- Total Containers
- CBM
- HTS Code

### PDF 2 - Sea Waybill Document

- Sea waybill no
- Voyage no
- Booking Ref
- Port of Discharge
- Date of issue
- Onboard date
- SCAC code

## Repository Structure

```text
entity-extraction-matching-genai/
|
├── app.py
├── main.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
|
├── config/
│   └── entity_fields.json
|
├── src/
│   └── entity_project/
│       ├── __init__.py
│       ├── pdf_utils.py
│       ├── gemini_extractor.py
│       ├── huggingface_ner.py
│       ├── matching.py
│       ├── excel_export.py
│       └── workflow.py
|
├── tests/
│   ├── test_matching.py
│   └── test_gemini_parser.py
|
└── sample_documents/
    └── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/entity-extraction-matching-genai.git
```

### 2. Navigate to the project

```bash
cd entity-extraction-matching-genai
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Gemini API

Copy `.env.example` to `.env`.

Add your private Gemini API key:

```text
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-3.8-flash
HF_NER_MODEL=dslim/bert-base-NER
```

Never upload your `.env` file to GitHub.

## Run the Project

### Streamlit application

```bash
streamlit run app.py
```

Upload both PDF documents and click Extract and Compare.

### Command-line execution

```bash
python main.py OBOL_SAMPLE.pdf SWB_SAMPLE.pdf
```

The extracted entities and matching results are exported to an Excel workbook.

## Excel Output

The generated workbook contains four sheets:

1. PDF 1 - Gemini
2. PDF 2 - Gemini
3. Hugging Face NER
4. Entity Matching

## Testing

Run unit tests using:

```bash
python -m unittest discover -s tests -v
```

The tests cover:
- Entity value normalization.
- Exact entity matching.
- Similarity-based candidate matching.
- Unmatched entity identification.
- Gemini response parsing.
- Missing entity handling.

## Hugging Face Implementation Note

The project includes a public pretrained BERT-based NER checkpoint for general entity recognition.

The supplied original Colab notebook demonstrates Gemini-based extraction and matching. It does not contain the original Hugging Face fine-tuning code or custom model checkpoint. The included BERT integration is therefore an inference component, not a reproduction of the original fine-tuning experiment.

## Limitations

- Scanned PDFs may require OCR.
- Generative AI extraction can produce incorrect or incomplete values.
- General-purpose NER may not identify every shipping-specific field.
- Similarity scores are candidate indicators and require manual verification.

## Security

Do not upload confidential PDF documents, private API keys or generated Excel files to a public repository.

Store API credentials in a local `.env` file.

## Author

Pranjal Ladde

Entity Extraction & Matching using Generative AI and NLP.
