from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from langchain_openai import AzureChatOpenAI

from write_a_book_with_flows.types import Chapter

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
class WriteBookChapterCrew:
    """Write Book Chapter Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
#    llm = AzureChatOpenAI(
#        openai_api_version=os.environ.get("AZURE_OPENAI_VERSION", "2023-07-01-preview"),
#        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt35"),
#        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://<your-endpoint>.openai.azure.com/"),
#        api_key=os.environ.get("AZURE_OPENAI_KEY")
#    )

    @agent
    def researcher(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config["researcher"],
            tools=[search_tool],
            verbose=True,
            llm=getLLM()
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            verbose=True,
            llm=getLLM()
        )

    @task
    def research_chapter(self) -> Task:
        return Task(
            config=self.tasks_config["research_chapter"],
        )

    @task
    def write_chapter(self) -> Task:
        return Task(
            config=self.tasks_config["write_chapter"],
            output_pydantic=Chapter
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Write Book Chapter Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
