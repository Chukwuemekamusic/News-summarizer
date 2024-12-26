import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import json
import time
from datetime import datetime, timedelta
import logging
import streamlit as st
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

class NewsAPIClient:
    def __init__(self):
        self.api_key = os.environ.get("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = 'https://newsapi.org/v2/everything'
        
    def get_news(self, topic: str, start_date: str = None) -> List[str]:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
        params = {
            'q': topic,
            'from': start_date,
            'sortBy': 'popularity',
            'apiKey': self.api_key,
            'pageSize': 5
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [self._format_article(article) for article in data.get("articles", [])]
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error occurred during API Request: {e}")
            return []
            
    def _format_article(self, article: Dict) -> str:
        return f"""
        Source: {article.get("source", {}).get("name", "Unknown")},
        Title: {article.get("title", "No title")},
        Description: {article.get("description", "No description")},
        URL: {article.get("url", "No URL")},
        Content: {article.get("content", "No content")},
        Published At: {article.get("publishedAt", "Unknown date")}
        """

class AssistantManager:
    def __init__(self, model: str = 'gpt-3.5-turbo-16k'):
        self.client = OpenAI()
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None
        self.news_client = NewsAPIClient()
        
        # Configuration
        self.ASSISTANT_CONFIG = {
            "name": "News Summarizer",
            "instructions": "You are a news summarizer. You will be given a list of news articles and you will need to summarize them. You will also provide the URL link to the news article if available",
            "run_instructions": "You will be given a list of news articles and you will need to summarize them.",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_news",
                        "description": "Get news articles from the internet",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                    "description": "The topic for the news, e.g. bitcoin",
                                }, 
                                "start_date": {
                                    "type": "string",
                                    "description": "The start date for the news filtering",
                                }
                            },
                            "required": ["topic"],
                        },
                    },
                },
            ]
        }
    
    def create_assistant(self, custom_config: Dict = None) -> None:
        """Creates an OpenAI assistant with given or default configuration."""
        if self.assistant is None:
            try:
                config = custom_config or self.ASSISTANT_CONFIG
                self.assistant = self.client.beta.assistants.create(
                    name=config["name"],
                    instructions=config["instructions"],
                    tools=config["tools"],
                    model=self.model
                )
                logging.info(f"Assistant created: {self.assistant.id}")
            except Exception as e:
                logging.error(f"Error creating assistant: {e}")
                raise

    def process_news_request(self, topic: str, custom_instructions: str = None) -> Optional[str]:
        """Process a news summarization request end-to-end."""
        try:
            self.create_thread()
            self.create_assistant()
            self.add_message_to_thread("user", f"summarize the news on this topic {topic}")
            self.run_assistant(custom_instructions)
            self.wait_for_completion()
            return self.summary
        except Exception as e:
            logging.error(f"Error processing news request: {e}")
            return None

    def create_thread(self) -> None:
        """Create a new thread for the assistant."""
        if not self.thread:
            try:
                self.thread = self.client.beta.threads.create()
                logging.info(f"Thread created: {self.thread.id}")
            except Exception as e:
                logging.error(f"Error creating thread: {e}")
                raise
            
    def add_message_to_thread(self, role: str, content: str) -> None:
        """Add a message to the thread."""
        if not self.thread:
            self.create_thread()
        try:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role=role,
                content=content
            )
            logging.info(f"Message added to thread: {content}")
        except Exception as e:
            logging.error(f"Error adding message to thread: {e}")
            raise
        
    def run_assistant(self, custom_instructions: str = None) -> None:
        """Runs the assistant with optional custom instructions."""
        if not self.assistant:
            raise ValueError("Assistant not initialized")
        if not self.thread:
            raise ValueError("Thread not initialized")
            
        try:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
                instructions=custom_instructions or self.ASSISTANT_CONFIG["run_instructions"]
            )
            logging.info(f"Run created: {self.run.id}")
        except Exception as e:
            logging.error(f"Error running assistant: {e}")
            raise
    
    def handle_required_actions(self, required_actions: Dict) -> None:
        """Handles any required actions from the assistant, such as function calls."""
        if not self.run:
            raise ValueError("Run not initialized")
            
        tool_outputs = []
        
        try:
            for action in required_actions["tool_calls"]:
                tool_call_id = action['id']
                func_name = action['function']['name']
                func_args = json.loads(action['function']['arguments'])
                
                if func_name == "get_news":
                    output = self.news_client.get_news(
                        topic=func_args['topic'],
                        start_date=func_args.get('start_date')
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": json.dumps(''.join(output))
                    })
                else:
                    raise ValueError(f"Unknown function: {func_name}")
                    
            logging.info("Submitting tool outputs to assistant")
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=self.run.id,
                tool_outputs=tool_outputs
            )
            
        except Exception as e:
            logging.error(f"Error handling required actions: {e}")
            raise

    def process_messages(self) -> None:
        """Processes messages from the thread and extracts the summary."""
        if not self.thread:
            raise ValueError("Thread not initialized")
            
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id
            )
            
            if messages.data:
                last_message = messages.data[0]
                if last_message.role == "assistant" and last_message.content:
                    self.summary = last_message.content[0].text.value
                    logging.info(f"Summary processed from {last_message.role}")
                else:
                    logging.warning("No assistant message or content found")
            else:
                logging.warning("No messages found in thread")
                
        except Exception as e:
            logging.error(f"Error processing messages: {e}")
            raise
            
    def wait_for_completion(self, interval: int = 2, timeout: int = 100) -> None:
        """Wait for the assistant's run to complete with improved error handling."""
        if not (self.thread and self.run):
            raise ValueError("Thread or Run not initialized")
            
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("Assistant run timed out")
                
            time.sleep(interval)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=self.run.id
            )
            
            logging.info(f"Run status: {run.status}")
            
            if run.status == "completed":
                self.process_messages()
                break
            elif run.status == "requires_action":
                self.handle_required_actions(run.required_action.submit_tool_outputs.model_dump())
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")
    
                
def create_streamlit_app():
    st.set_page_config(page_title="News Summarizer", layout="wide")
    
    if "manager" not in st.session_state:
        st.session_state.manager = AssistantManager()
    
    st.title("📰 News Summarizer")
    
    with st.form(key="news_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            topic = st.text_input("Enter a topic to summarize", placeholder="e.g., artificial intelligence")
        with col2:
            days_ago = st.number_input("Days of news to fetch", min_value=1, max_value=30, value=7)
        submit = st.form_submit_button("Get Summary")
        
    if submit and topic:
        with st.spinner("Fetching and summarizing news..."):
            try:
                summary = st.session_state.manager.process_news_request(
                    topic,
                    f"Summarize the last {days_ago} days of news about {topic}"
                )
                if summary:
                    st.success("Summary generated successfully!")
                    st.markdown(summary)
                else:
                    st.error("Failed to generate summary. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    create_streamlit_app()