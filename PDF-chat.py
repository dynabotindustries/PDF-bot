import os
import sys
from dotenv import load_dotenv

# --- Gemini File API & LLM Libraries ---
from google import genai
from google.genai.errors import APIError
from google.genai import types
import pathlib
import httpx 

# --- PyQt6 Libraries (Imports are the same) ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QFileDialog, QMessageBox, QLabel
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QStandardPaths

# --- RAG Helper Class (Simplified & Corrected) ---

class SimpleQASystem:
    """Handles PDF upload via File API and LLM interaction."""
    
    def __init__(self, api_key):
        """Initializes the Gemini client."""
        if not api_key:
            raise ValueError("API Key is missing.")
            
        self.client = genai.Client(api_key=api_key)
        self.uploaded_file_ref = None # Stores the file object reference from the API
        self.llm_model = "gemini-2.5-flash" # The model to use

    def upload_pdf(self, pdf_path):
        """Uploads the PDF using the File API."""
        
        # Clean up any previously uploaded file to save space/cost
        self.cleanup_file()
        
        try:
            # 1. Upload the PDF
            pdf_path_obj = pathlib.Path(pdf_path)
            
            # --- FIX APPLIED HERE: Removed 'display_name' keyword ---
            self.uploaded_file_ref = self.client.files.upload(
                file=pdf_path_obj,
                # display_name=pdf_path_obj.name # <--- REMOVED
            )
            # --------------------------------------------------------
            
            return True
        except APIError as e:
            print(f"Gemini API Error during file upload: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def ask_question(self, question):
        """Passes the file reference and the question to the LLM."""
        if not self.uploaded_file_ref:
            return "Error: No document has been successfully uploaded."
            
        try:
            # Send the file reference AND the text prompt in the contents list
            response = self.client.models.generate_content(
                model=self.llm_model,
                contents=[self.uploaded_file_ref, question]
            )
            return response.text
        except APIError as e:
            return f"Gemini API Error during generation: {e}"
            
    def cleanup_file(self):
        """Deletes the file from the Gemini File API."""
        if self.uploaded_file_ref:
            try:
                self.client.files.delete(name=self.uploaded_file_ref.name)
                print(f"Cleaned up file: {self.uploaded_file_ref.name}")
            except APIError as e:
                print(f"Error cleaning up file: {e}")
            finally:
                self.uploaded_file_ref = None


# --- PyQt Worker Thread (Same) ---

class Worker(QThread):
    """A worker to run the API calls off the main thread."""
    result = pyqtSignal(str, bool) # Signal(message, is_success)

    def __init__(self, qa_system, task_type, **kwargs):
        super().__init__()
        self.qa_system = qa_system
        self.task_type = task_type
        self.kwargs = kwargs

    def run(self):
        if self.task_type == "upload_pdf":
            pdf_path = self.kwargs.get("pdf_path")
            success = self.qa_system.upload_pdf(pdf_path)
            message = "PDF uploaded successfully. You can now ask questions." if success else "Error uploading PDF."
            self.result.emit(message, success)
            
        elif self.task_type == "ask_question":
            question = self.kwargs.get("question")
            response = self.qa_system.ask_question(question)
            self.result.emit(response, True) 

# --- PyQt Main Application (Same) ---

class ChatbotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            QMessageBox.critical(self, "API Key Error", "GEMINI_API_KEY not found in .env file.")
            sys.exit(-1)
            
        self.qa_system = SimpleQASystem(api_key)
        self.init_ui()
        self.pdf_processed = False
        
        # Ensure cleanup when the app closes
        QApplication.instance().aboutToQuit.connect(self.qa_system.cleanup_file)

    def init_ui(self):
        self.setWindowTitle("Gemini File API Chatbot (PyQt)")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. PDF Upload Section
        pdf_layout = QHBoxLayout()
        self.pdf_label = QLabel("No PDF loaded.")
        self.upload_button = QPushButton("Select & Upload PDF")
        self.upload_button.clicked.connect(self.select_and_upload_pdf)
        pdf_layout.addWidget(self.pdf_label)
        pdf_layout.addWidget(self.upload_button)
        main_layout.addLayout(pdf_layout)

        # 2. Chat History Display
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setText("Welcome to the Gemini File API Chatbot.\n\n1. Select and upload a PDF.\n2. Ask a question about the entire document.")
        main_layout.addWidget(self.chat_history)

        # 3. User Input Section
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask your question here...")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_question)
        self.question_input.returnPressed.connect(self.send_question) 

        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.send_button)
        main_layout.addLayout(input_layout)
        
        self.set_ui_enabled(False) # Disable input until PDF is processed

    def set_ui_enabled(self, enabled):
        """Enables/disables the chat input controls."""
        self.question_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

    def select_and_upload_pdf(self):
        """Opens file dialog and starts the PDF upload thread."""
        initial_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", initial_dir, "PDF Files (*.pdf)"
        )
        
        if file_name:
            self.pdf_label.setText(f"Uploading: {os.path.basename(file_name)}...")
            self.upload_button.setEnabled(False)
            self.set_ui_enabled(False) # Disable chat during upload
            self.chat_history.append(f"--- Uploading {os.path.basename(file_name)}... ---")
            
            # Start worker thread for processing
            self.worker = Worker(self.qa_system, "upload_pdf", pdf_path=file_name)
            self.worker.result.connect(self.handle_upload_result)
            self.worker.start()

    def handle_upload_result(self, message, is_success):
        """Handles the result from the PDF upload worker."""
        self.chat_history.append(message)
        self.upload_button.setEnabled(True)
        
        if is_success:
            self.pdf_processed = True
            self.set_ui_enabled(True)
            self.pdf_label.setText("PDF Ready! Ask your questions.")
        else:
            self.pdf_processed = False
            self.pdf_label.setText("Error uploading PDF. Please try again.")

    def send_question(self):
        """Starts the question answering thread."""
        question = self.question_input.text().strip()
        if not question:
            return
            
        if not self.pdf_processed:
            QMessageBox.warning(self, "Warning", "Please upload a PDF first.")
            return

        self.chat_history.append(f"\nUser: {question}")
        self.question_input.clear()
        self.set_ui_enabled(False) # Disable while waiting for response
        self.chat_history.append("Gemini: Thinking...")

        # Start worker thread for asking question
        self.worker = Worker(self.qa_system, "ask_question", question=question)
        self.worker.result.connect(self.handle_question_result)
        self.worker.start()

    def handle_question_result(self, response, is_success):
        """Handles the result from the question answering worker."""
        # Replace the "Thinking..." message with the final response
        current_text = self.chat_history.toPlainText()
        current_text = current_text.replace("Gemini: Thinking...", f"Gemini: {response}")
        self.chat_history.setText(current_text)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

        self.set_ui_enabled(True) # Re-enable input


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatbotApp()
    window.show()
    sys.exit(app.exec())
