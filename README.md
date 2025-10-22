# Gemini PDF Chatbot (PyQt Desktop App)

A simple, non-blocking desktop chatbot built with Python's PyQt6, designed to allow users to upload PDF documents and ask questions about their content using the Google Gemini API's powerful File and Generation capabilities.

## 🌟 Features

*   **Desktop Interface:** A native application experience powered by PyQt6.
*   **Simple Document QA:** Upload a PDF and ask questions directly related to its content.
*   **Gemini File API Integration:** Leverages the native Gemini File API (`client.files.upload`) to handle document parsing and context injection, eliminating the need for complex RAG pipelines (chunking, vector stores) for medium-to-large files.
*   **Non-Blocking UI:** Uses Python threading (`QThread`) to run time-consuming API calls in the background, ensuring the application remains responsive.
*   **Automatic Cleanup:** Ensures uploaded files are automatically deleted from the Gemini service when the application is closed.

## 📋 Prerequisites

Before you begin, ensure you have the following:

1.  **Python:** Python 3.8+ installed on your system.
2.  **Gemini API Key:** An API key obtained from Google AI Studio.
3.  **Environment Setup:** Create a file named `.env` in the project directory and add your API key:

    ```
    # .env file
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

## 🛠️ Installation

1.  **Clone the Repository (or Download the File):**

    The project file is located at the following URL:
    [https://github.com/dynabotindustries/PDF-bot/blob/main/PDF-chat.py](https://github.com/dynabotindustries/PDF-bot/blob/main/PDF-chat.py)

    Save the file as `PDF-chat.py` in your local project directory.

2.  **Install Dependencies:**

    Install all required Python libraries using pip:

    ```bash
    pip install google-genai PyQt6 python-dotenv httpx pathlib
    ```

    > **Note:** The `httpx` and `pathlib` libraries are often included with standard Python installations but are explicitly mentioned here as they are dependencies for the File API process.

## 🚀 How to Run

1.  Ensure your `.env` file is set up correctly.
2.  Run the main application file from your terminal:

    ```bash
    python PDF-chat.py
    ```

## 💡 Project Evolution: RAG vs. File API

The initial goal of this project was a standard RAG (Retrieval-Augmented Generation) Chatbot, which involves:

### Previous (Classic RAG) Implementation:
| Step | Technique | Purpose |
| :--- | :--- | :--- |
| **1.** | **Chunking (PyPDF2)** | Break the PDF text into small pieces (e.g., 1000 characters). |
| **2.** | **Embedding (Gemini)** | Convert each chunk into a high-dimensional vector. |
| **3.** | **Vector Store (FAISS)** | Store all vectors in a searchable index. |
| **4.** | **Retrieval** | Embed the user's question and search the vector store for the top K similar text chunks. |
| **5.** | **Generation (Gemini)** | Pass only the retrieved chunks and the question to the LLM for the final answer. |

This classic RAG approach is **highly effective and scalable** for documents that are **too large** for a single LLM context window (hundreds of thousands of tokens).

### Current (File API) Implementation:
| Technique | Reason for Switch | Advantage |
| :--- | :--- | :--- |
| **Gemini File API** | Simplicity and direct multimodal support. | **Vastly simpler code.** The need for PyPDF2, chunking, embeddings, and FAISS is eliminated. The Gemini model handles the parsing and intelligent context management for the entire document internally, making development faster and cleaner for documents within the model's context limits. |

We switched to the **File API** to embrace the simplicity and power of the native Gemini platform, providing a **more streamlined and elegant solution** for a simple PDF chatbot.

## 📝 Usage

1.  **Select & Upload PDF:** Click the **"Select & Upload PDF"** button. A file dialog will open. Select your PDF document.
2.  **Wait for Upload:** The UI will display a "Uploading..." message. Wait for the API to process and upload the file. When complete, the status will change to **"PDF Ready! Ask your questions."**
3.  **Ask Questions:** Type your question in the input box (e.g., "What is the main conclusion of the report?") and click **"Send."**
4.  **Receive Answer:** The response will appear in the chat history. Since the LLM receives the entire file, it can answer questions based on the full document's content.

## 🗑️ Cleanup Note

The application is designed to automatically call the `client.files.delete()` method when you close the PyQt window. This is important as files uploaded to the Gemini File API consume storage and may incur costs if left undeleted.

***
## 📄 Dependencies

*   `google-genai`
*   `PyQt6`
*   `python-dotenv`
*   `pathlib`
*   `httpx`

***
## 📜 License

This project is open-source. (Add your chosen license here, e.g., MIT, Apache 2.0).
