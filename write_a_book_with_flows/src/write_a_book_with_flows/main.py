#!/usr/bin/env python
import asyncio
from typing import List

# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from write_a_book_with_flows.crews.write_book_chapter_crew.write_book_chapter_crew import (
    WriteBookChapterCrew,
)
from write_a_book_with_flows.types import Chapter, ChapterOutline

from .crews.outline_book_crew.outline_crew import OutlineCrew

import os
from dotenv import load_dotenv
load_dotenv()

from langtrace_python_sdk import langtrace # Must precede any llm module imports
langtrace.init(api_key = os.environ.get("LANGTRACE_API_KEY", "abcdefg"))

def cache_function(*args):
    return False

class BookState(BaseModel):
    title: str = "Unterm Rad - Neuauflage 2024"
    book: List[Chapter] = []
    book_outline: List[ChapterOutline] = []
    topic: str = (
        "Neuschreibung des Romans 'Unterm Rad' von Hermann Hesse mit einer weiblichen Hauptfigur und in die moderne Zeit des Jahres 2024 übertragen."
    )
    goal: str = """
        Das Ziel dieses Buches ist es, den Roman "Unterm Rad" von Hermann Hesse im exakt gleichen Stil wie das Original neu zu schreiben, jedoch mit einer weiblichen Hauptfigur und in die moderne Zeit des Jahres 2024 übertragen.
        Das Buch soll in Schweizer Hochdeutsch verfasst werden.
    """

class BookFlow(Flow[BookState]):
    initial_state = BookState

    @start()
    def generate_book_outline(self):
        print("Kickoff the Book Outline Crew")
        output = (
            OutlineCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topic, "goal": self.state.goal})
        )


        print("Full raw Outline output:", output)

        chapters = output["chapters"]
        print("Chapters:", chapters)

        self.state.book_outline = chapters
        print("Finished the Book Outline Crew")
        return chapters

    @listen(generate_book_outline)
    async def write_chapters(self):
        print("Writing Book Chapters")
        tasks = []

        async def write_single_chapter(chapter_outline):
            output = (
                WriteBookChapterCrew()
                .crew()
                .kickoff(
                    inputs={
                        "goal": self.state.goal,
                        "topic": self.state.topic,
                        "chapter_title": chapter_outline.title,
                        "chapter_description": chapter_outline.description,
                        "book_outline": [
                            chapter_outline.model_dump_json()
                            for chapter_outline in self.state.book_outline
                        ],
                    }
                )
            )

            print("Full raw Writer output:", output)

            title = output["title"]
            content = output["content"]
            chapter = Chapter(title=title, content=content)
            return chapter

        for chapter_outline in self.state.book_outline:
            print(f"Writing Chapter: {chapter_outline.title}")
            print(f"Description: {chapter_outline.description}")
            # Schedule each chapter writing task
            task = asyncio.create_task(write_single_chapter(chapter_outline))
            tasks.append(task)

        # Await all chapter writing tasks concurrently
        chapters = await asyncio.gather(*tasks)
        print("Newly generated chapters:", chapters)
        self.state.book.extend(chapters)

        print("Book Chapters", self.state.book)

    @listen(write_chapters)
    async def join_and_save_chapter(self):
        print("Joining and Saving Book Chapters")
        # Combine all chapters into a single markdown string
        book_content = ""

        for chapter in self.state.book:
            # Add the chapter title as an H1 heading
            book_content += f"# {chapter.title}\n\n"
            # Add the chapter content
            book_content += f"{chapter.content}\n\n"

        # The title of the book from self.state.title
        book_title = self.state.title

        # Create the filename by replacing spaces with underscores and adding .md extension
        filename = f"./{book_title.replace(' ', '_')}.md"

        # Save the combined content into the file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(book_content)

        print(f"Book saved as {filename}")
        return book_content


def kickoff():
    poem_flow = BookFlow()
    poem_flow.kickoff()


def plot():
    poem_flow = BookFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
