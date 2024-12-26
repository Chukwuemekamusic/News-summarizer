# 🗞 News Summarizer

A Python-based application to fetch and summarize news articles on any topic using OpenAI's GPT model and the News API. This project leverages `Streamlit` for an interactive user interface, making it easy to generate news summaries with just a few clicks.

## Features

- Fetches recent news articles from the News API based on user-provided topics.
- Summarizes the news using OpenAI's GPT model.
- Interactive UI for inputting topics and specifying date ranges.
- Logs and error handling for smoother debugging.

## Prerequisites

- Python 3.8 or higher
- A News API key (https://newsapi.org/)
- OpenAI API key
- `pip` for installing dependencies

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Chukwuemekamusic/News-summarizer
   cd News-summarizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following:
   ```env
   NEWS_API_KEY=your_news_api_key 
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run main.py
   ```

2. Open the app in your browser and input a topic to summarize news articles.

3. Adjust the date range as needed to fetch news from the desired period.

## Project Structure

- `NewsAPIClient`: Handles news fetching from the News API.
- `AssistantManager`: Manages interaction with OpenAI's GPT model for summarization.
- `Streamlit App`: Provides a user-friendly interface for inputs and outputs.

## Requirements

The project depends on the following libraries:
- `streamlit`
- `openai`
- `requests`
- `python-dotenv`
- `logging`

Install them using the `requirements.txt` file.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- [News API](https://newsapi.org/)
- [OpenAI](https://openai.com/)
- [Streamlit](https://streamlit.io/)

