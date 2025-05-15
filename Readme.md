# ScenarioCraft AI: AI-Powered Gherkin Scenario Generation


## 🚀 Project Overview

ScenarioCraft AI is an AI-powered tool designed to accelerate Behavior-Driven Development (BDD) by automatically generating Gherkin scenarios. It leverages AI to transform user stories or analyze website URLs into comprehensive `.feature` files.

## 🌟 Key Features

*   **AI Gherkin Generation (User Story):** Converts user stories into detailed Gherkin scenarios, including positive/negative cases where applicable.
*   **AI Gherkin Generation (URL):** Analyzes a website URL to generate Gherkin scenarios for verifying key UI elements (headings, links, images, icons, etc.).
*   **Gherkin Scenario Editor:** Review and refine the AI-generated Gherkin scenarios directly within the application before saving.
*   **Save & Download:** Save your edited scenarios and download them as standard `.feature` files.
*   **Category Stats (URL):** View statistics on the number of scenarios generated per element category when using the URL input.

## 🔧 Technology Stack

*   Python
*   Streamlit (for the UI)
*   AI Models (e.g., OpenAI GPT series via Langchain/Agno)
*   Playwright (for URL fetching/parsing)
*   BeautifulSoup4 (for HTML parsing)

## Prerequisites

- Python 3.9 or higher

## 📦 Installation

1.  **Clone the repository:**
    Replace `<your-repository-url>` with the actual URL.
    ```bash
    git clone <your-repository-url>
    cd ScenarioCraftAI # Or your repo directory name
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers (needed for URL fetching):**
    ```bash
    playwright install
    ```

5.  **Create environment file:**
    Create a `.env` file in the project's root directory and add your OpenAI API key:
    ```dotenv
    OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
    ```

6.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## 🖥️ Usage

1.  Launch the application using `streamlit run app.py`.
2.  Navigate using the tabs:
    *   **Generate from User Story:**
        *   Enter a user story into the text area.
        *   Click "Generate Gherkin".
        *   Review the generated scenarios in the editor.
        *   Edit as needed and click "Save Changes".
        *   Click "Download Gherkin (.feature)" to get the saved file.
    *   **Generate from URL:**
        *   Enter a website URL.
        *   Click "Generate Scenarios from URL".
        *   View the generation statistics.
        *   Review the generated scenarios in the editor.
        *   Edit as needed and click "Save Changes".
        *   Click "Download Gherkin (.feature)" to get the saved file.

## 🤔 Questions or Need Help?

*   Please open an issue on the GitHub repository for bug reports or feature requests.

## 🌈 Acknowledgments

*   Built using Streamlit, Langchain/Agno, OpenAI, Playwright, and BeautifulSoup.
*   Inspired by the need for efficient BDD scenario creation.

<!-- Removed outdated How it works, Changelog, and specific WaiGenie links -->
# GherkinGeneration
