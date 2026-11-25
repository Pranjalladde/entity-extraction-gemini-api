# Entity Extraction from PDF using Google Gemini API

A Python project that extracts business-specific entities from PDF documents using Google's Gemini API, LangChain's `PyPDFLoader`, and Pandas. Results are exported into an Excel workbook.

**This is the Gemini API project based on the supplied code. It does not use BERT.**

## Features

- Read PDF text page by page with LangChain `PyPDFLoader`.
- Split page text into blocks separated by blank lines.
- Send each block to Gemini with user-selected business fields.
- Parse Gemini responses in `ENTITY TYPE | extracted value` format.
- Consolidate values by entity type and retain page/block references.
- Export the results into an Excel workbook with summary and page-wise sheets.
- Run with a command-line interface or a Streamlit web interface.

## Default packing-list fields

- VESSEL
- ETD BUSAN
- NO.&Date of Invoice
- Shipper/Exporter
- TOTAL CIF
- PURCHASE ORDER NO.

Edit `config/entity_fields.json` or pass a different list of fields when running the command-line script.

## Tech stack

Python, Google Gemini API, `google-generativeai`, LangChain Community `PyPDFLoader`, pypdf, Pandas, OpenPyXL, python-dotenv, and Streamlit.

## Project structure

```text
entity-extraction-gemini-api/
├── app.py
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/
│   └── entity_fields.json
├── entity_extraction/
│   ├── __init__.py
│   └── pipeline.py
├── tests/
│   └── test_response_parser.py
└── sample_documents/
    └── README.md
```

## Setup

Use Python 3.10 or newer.

### 1. Create a Gemini API key

Create a Gemini API key in Google AI Studio and keep it private. The key pasted in the original code/chat should be treated as exposed: revoke that key and use a replacement. Do not commit an API key to GitHub.

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the API key locally

Copy `.env.example` to a new file named `.env`. Open `.env` and replace the placeholder with your new private key:

```text
GEMINI_API_KEY=your_new_private_api_key
GEMINI_MODEL=gemini-3.8-flash
```

The `.env` file is excluded by `.gitignore`. Do not upload it, share it in screenshots, or paste the key into Python files. Only `.env.example` belongs in the public repository.

### 5. Run from the command line

```bash
python main.py "path/to/packing-list.pdf"
```

The default output is `extracted_entities.xlsx`. To choose another output path:

```bash
python main.py "path/to/packing-list.pdf" --output "packing_list_results.xlsx"
```

To extract different fields:

```bash
python main.py "path/to/document.pdf" --fields "Invoice Number" "Invoice Date" "Vendor" "TOTAL CIF"
```

To select a different model ID:

```bash
python main.py "path/to/packing-list.pdf" --model gemini-3.8-flash
```

### 6. Run the Streamlit interface

```bash
streamlit run app.py
```

Upload a PDF, enter one entity field per line, click **Extract entities**, and download the Excel workbook.

## Excel output

The workbook contains two sheets:

| Sheet | Contents |
|---|---|
| Entities from PDF | Consolidated values grouped by requested entity type |
| Page-wise Results | Extracted values with source page and block numbers |

## How it works

1. `PyPDFLoader` reads selectable text from each PDF page.
2. The text is split into blocks separated by blank lines.
3. Each block is sent to Gemini with a prompt listing the requested entity fields.
4. Gemini returns one `ENTITY TYPE | extracted value` pair per line.
5. Python parses the returned pairs and consolidates values.
6. Pandas and OpenPyXL write the summary and page-wise values into Excel.

## Model and SDK notes

- The model ID is configurable through `GEMINI_MODEL`. This project uses `gemini-3.8-flash` as its example default; check Google's [current model list](https://ai.google.dev/gemini-api/docs/models) for model availability in your account.
- This package retains the original SDK style, `import google.generativeai as genai`, to match the code supplied for this project.
- Google deprecated the `google-generativeai` Python SDK on November 30, 2025 and ended support for it. Google recommends the newer `google-genai` SDK. This repository keeps the old SDK at your request, but it is legacy and may fail with newer models or API features. See [Google's SDK guidance](https://ai.google.dev/gemini-api/docs/libraries) and the [archived legacy SDK repository](https://github.com/google-gemini/deprecated-generative-ai-python).

## Limitations

- Scanned/image-only PDFs may require OCR before `PyPDFLoader` can extract text.
- Gemini can omit or misread values. Review the Excel output before using it in business workflows.
- Each text block can generate a separate API request and consume API quota.
- The default entity fields are tailored to a packing-list example; change the fields for other document types.

## Privacy and security

Do not commit confidential invoices, packing lists, purchase orders, customer data, or vendor documents. Store your API key only in your local `.env` file. Revoke any exposed key and replace it.
