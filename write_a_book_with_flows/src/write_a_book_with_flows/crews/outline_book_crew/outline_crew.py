from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from langchain_openai import AzureChatOpenAI

from write_a_book_with_flows.types import BookOutline

import os
from dotenv import load_dotenv

load_dotenv()
from langtrace_python_sdk import langtrace # Must precede any llm module imports
langtrace.init(api_key = os.environ.get("LANGTRACE_API_KEY", "abcdefg"))

from crewai import LLM
def getLLM():
    return LLM(
        model="azure/gpt-4o-mini",
        api_version=os.environ.get("AZURE_OPENAI_VERSION", "2023-07-01-preview"),
        api_key=os.environ.get("AZURE_OPENAI_KEY"),
        base_url=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://<your-endpoint>.openai.azure.com/")
    )

@CrewBase
class OutlineCrew:
    """Book Outline Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"


#    default_llm = AzureChatOpenAI(
#        api_version=os.environ.get("AZURE_OPENAI_VERSION", "2023-07-01-preview"),
#        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt35"),
##        base_url=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://api.openai.azure.com/"),
#        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://<your-endpoint>.openai.azure.com/"),
#        api_key=os.environ.get("AZURE_OPENAI_KEY")
#    )

    @agent
    def researcher(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config["researcher"],
            tools=[search_tool],
            llm=getLLM(),
            verbose=True
        )

    @agent
    def outliner(self) -> Agent:
        return Agent(
            config=self.agents_config["outliner"],
            llm=getLLM(),
            verbose=True
        )

    @task
    def research_topic(self) -> Task:
        return Task(
            config=self.tasks_config["research_topic"],
        )

    @task
    def generate_outline(self) -> Task:
        return Task(
            config=self.tasks_config["generate_outline"], output_pydantic=BookOutline
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Book Outline Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
