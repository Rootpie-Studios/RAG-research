import streamlit as st
import base64
import requests
from io import BytesIO
from PIL import Image

# Set page config
st.set_page_config(
    page_title="Mistral OCR Document Processor", page_icon="📄", layout="wide"
)

# Title and description
st.title("📄 Mistral OCR Document Processor")
st.markdown("""
This application allows you to upload documents, process them with Mistral OCR,
and extract text content. Supported formats: PDF, JPG, PNG.
""")

# API configuration
API_KEY = st.sidebar.text_input("Enter your Mistral API Key", type="password")
API_URL = "https://api.mistral.ai/v1/ocr"

# File uploader
uploaded_files = st.file_uploader(
    "Upload documents (PDF, JPG, PNG)",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

# Initialize session state for processed files
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

# Process files when API key is provided and files are uploaded
if API_KEY and uploaded_files:
    with st.spinner("Processing documents..."):
        for file in uploaded_files:
            # Convert to base64
            file_content = file.read()
            encoded_file = base64.b64encode(file_content).decode("utf-8")

            # Prepare request payload
            payload = {
                "file": encoded_file,
                "filename": file.name,
                "mime_type": file.type,
            }

            # Make API call to Mistral OCR
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post(API_URL, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                extracted_text = result.get("text", "No text extracted")

                # Store results
                st.session_state.processed_files.append(
                    {
                        "filename": file.name,
                        "content": extracted_text,
                        "status": "success",
                    }
                )

            except requests.exceptions.RequestException as e:
                st.session_state.processed_files.append(
                    {
                        "filename": file.name,
                        "content": f"Error: {str(e)}",
                        "status": "error",
                    }
                )

# Display results
if st.session_state.processed_files:
    st.subheader("Extracted Text Results")

    for i, result in enumerate(st.session_state.processed_files):
        with st.expander(f"{result['filename']} ({result['status'].upper()})"):
            if result["status"] == "success":
                st.text_area(
                    label="Extracted Text",
                    value=result["content"],
                    height=200,
                    key=f"text_{i}",
                )

                # Download button
                st.download_button(
                    label="Download Text",
                    data=result["content"],
                    file_name=f"{result['filename']}_extracted.txt",
                    mime="text/plain",
                )
            else:
                st.error(result["content"])

# Instructions section
st.sidebar.markdown("---")
st.sidebar.subheader("Instructions")
st.sidebar.markdown("""
1. Get your Mistral API key from [Mistral AI](https://console.mistral.ai/)
2. Enter your API key in the input above
3. Upload documents (PDF, JPG, PNG)
4. Click "Process" to extract text
5. View and download results
""")
