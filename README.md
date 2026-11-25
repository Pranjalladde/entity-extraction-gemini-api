# Entity Extraction & Matching from PDFs using GenAI

A Python project for extracting entities from two related PDF documents (for example, an OBOL document and a Sea Waybill), identifying common named entities, comparing extracted values, and exporting the results to Excel.

## What the supplied sample demonstrates

The supplied Colab notebook demonstrates:
- Loading two PDFs with LangChain `PyPDFLoader`.
- Calling Google Gemini with prompts to extract logistics fields from each PDF.
- Extracting fields such as booking number, address, order number, vessel name, OBOL number, sea waybill number, voyage number, dates, destination port, and SCAC code.
- Saving extracted values to Excel.
- Comparing extracted values across the two documents.

The supplied notebook uses Gemini and LangChain. It does not include Hugging Face fine-tuning code or a custom BERT checkpoint.

## Components in this GitHub version

1. **Gemini extraction:** Uses the Gemini API to extract document-specific shipping fields from both PDFs.
2. **Hugging Face NER:** Uses a public pretrained BERT token-classification checkpoint for general entity recognition (person, organisation, location, miscellaneous).
3. **Entity matching:** Compares Gemini-extracted values across the two PDFs using normalized exact matching and a high-similarity candidate check.
4. **Excel reporting:** Exports PDF 1 extraction, PDF 2 extraction, Hugging Face NER, and cross-document comparisons into separate worksheets.
5. **User interface:** Offers a Streamlit interface and a command-line workflow.

## Technologies

Python, Google Gemini API, `google-genai`, LangChain Community `PyPDFLoader`, pypdf, Hugging Face Transformers, BERT NER, Pandas, OpenPyXL, python-dotenv, Streamlit.

## Default fields

### OBOL document (PDF 1)
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

### Sea Waybill document (PDF 2)
- Sea waybill no
- Voyage no
- Booking Ref
- Port of Discharge
- Date of issue
- Onboard date
- SCAC code

Edit `config/entity_fields.json` to change these field lists.

## Project structure

```text
entity-extraction-matching-genai/
├── app.py
├── main.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   └── entity_fields.json
├── src/
│   └── entity_project/
│       ├── __init__.py
│       ├── pdf_utils.py
│       ├── gemini_extractor.py
│       ├── huggingface_ner.py
│       ├── matching.py
│       ├── excel_export.py
│       └── workflow.py
├── tests/
│   ├── test_gemini_parser.py
│   └── test_matching.py
└── sample_documents/
    └── README.md
```

## Setup

Use Python 3.10 or newer.

### 1. Create a virtual environment

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

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PyTorch installation can depend on CPU/GPU and operating system. For a specific PyTorch build, use the official PyTorch installation selector.

### 3. Configure Gemini securely

Create a new Gemini API key. Any key pasted into the earlier notebook, chat, or public repository should be considered exposed: revoke it and generate a replacement.

Copy `.env.example` to `.env` and edit it locally:

```text
GEMINI_API_KEY=your_new_private_key
GEMINI_MODEL=gemini-3.8-flash
HF_NER_MODEL=dslim/bert-base-NER
HF_TOKEN=
```

The `.env` file is excluded by `.gitignore`. Never upload `.env`, API keys, PDFs, or generated Excel files to GitHub.

### 4. Run the Streamlit interface

```bash
streamlit run app.py
```

Upload the OBOL PDF and Sea Waybill PDF, then select **Extract and compare**. The first Hugging Face run downloads the pretrained checkpoint and may take some time.

### 5. Run from the command line

```bash
python main.py "path/to/OBOL_SAMPLE.pdf" "path/to/SWB_SAMPLE.pdf"
```

Set a report filename:

```bash
python main.py "OBOL_SAMPLE.pdf" "SWB_SAMPLE.pdf" --output "entity_comparison.xlsx"
```

Set model IDs:

```bash
python main.py "OBOL_SAMPLE.pdf" "SWB_SAMPLE.pdf" --gemini-model gemini-3.8-flash --hf-model dslim/bert-base-NER
```

## Excel output

The workbook contains four sheets:
- **PDF 1 - Gemini:** Gemini-extracted fields from the first PDF.
- **PDF 2 - Gemini:** Gemini-extracted fields from the second PDF.
- **Hugging Face NER:** General BERT NER entities with confidence scores.
- **Entity Matching:** Exact matches, similar candidates, unmatched PDF 1 values, and values only in PDF 2.

## How matching works

Values are normalized by removing punctuation and spaces and converting to lowercase. Normalized exact matches are labelled **Exact match**. Values above the configured text-similarity threshold are labelled **Similar candidate**. Values without a qualifying partner are retained as unmatched.

A text similarity score is only a comparison aid. It does not prove two people, shipments, or records are the same. Review possible matches manually.

## Hugging Face implementation note

This repository includes an inference integration using the public pretrained checkpoint `dslim/bert-base-NER`. This checkpoint is used to recognize general entities such as persons, organizations, locations, and miscellaneous entities.

The supplied Colab notebook and project PPT do not include the original Hugging Face training script, labelled fine-tuning dataset, or custom model checkpoint. Therefore, this GitHub version does not claim to reproduce a custom fine-tuning run. If you have your original fine-tuned Hugging Face model, set `HF_NER_MODEL` to its local path or Hugging Face model repository.

The BERT NER component complements Gemini's prompt-based extraction of logistics-specific fields. General-purpose NER models may not identify domain-specific values such as booking references or waybill numbers; Gemini extraction is used for those fields.

## Model and SDK notes

- The original notebook used `google.generativeai` and the old `gemini-1.0-pro` model ID. This project uses Google's current `google-genai` Python SDK and defaults to `gemini-3.8-flash`. Model availability can vary by account; check Google's live model documentation before changing the model ID.
- Public Hugging Face models generally do not require `HF_TOKEN`. A token may be needed for private or gated model repositories.
- API use is subject to Gemini quotas and pricing.

## Limitations

- Scanned or image-only PDFs need OCR before `PyPDFLoader` can extract text.
- Gemini can omit or misread fields; review the workbook.
- General-purpose BERT NER is not trained specifically for shipping terminology.
- The similarity function finds candidate strings; it is not a domain-trained identity resolution model.
- Large PDFs can require multiple Gemini requests and take longer to process.

## Privacy and security

Do not commit real shipment documents, sea waybills, invoices, customer information, generated Excel files, or API keys. Use approved non-confidential or synthetic PDFs for public demonstrations. Keep credentials in your local `.env` file only.
