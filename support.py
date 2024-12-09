import os
import json
import requests
from database import Database

from openai import OpenAI
client = OpenAI()

from dotenv import load_dotenv
load_dotenv(override=True)

class SupportService:
    def __init__(self):
        self.db = Database()

    def download_pdf(self, url):
        if ".pdf" in url and "/" in url:
            local_file = url.split("/")[-1]

            response = requests.get(url, stream=True)
            response.raise_for_status()

            if 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(local_file, 'wb') as pdf_file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            pdf_file.write(chunk)

            if os.path.exists(local_file):
                return local_file

    def get_primary_assistant(self):
        sql = """SELECT assistant_id 
                 FROM assistants 
                 WHERE is_primary = 1;"""

        assistants = self.db.select_all(sql)
        if assistants:
            return assistants[0]['assistant_id']

    def get_primary_vector_store(self):
        sql = """SELECT assistant_id 
                 FROM assistants 
                 WHERE is_primary = 1;"""

        assistants = self.db.select_all(sql)
        if assistants:
            return assistants[0]['assistant_id']

    def compose_language(self):
        data = self.db.select_all(
            """SELECT b.block_id, b.category, b.chapter, b.section, b.article, b.segment, 
                  b.text, b.amendments, 
                  b.is_annulled, b.is_amended, b.is_superseded,
                  catm.subtitle AS category_subtitle, 
                  chm.subtitle AS chapter_subtitle, 
                  sm.subtitle AS section_subtitle,
                  am.ratified AS amendment_ratified
               FROM blocks b
                  LEFT JOIN category_metadata catm USING (category)
                  LEFT JOIN chapter_metadata chm ON (
                     chm.category = b.category AND 
                     chm.chapter = b.chapter
                  )
                  LEFT JOIN section_metadata sm ON (
                     sm.category = b.category AND 
                     sm.chapter = b.chapter AND 
                     sm.section = b.section
                  )
                  LEFT JOIN amendment_metadata am ON (
                     b.category = 'amendment' AND 
                     am.article = b.article
                  );"""
        )

        output = []
        if data:
            for block in data:
                chapter_block = None
                if block['chapter']:
                    chapter_block = {
                        "number": block['chapter'],
                        "subtitle": block['chapter_subtitle'],
                    }

                section_block = None
                if block['section']:
                    section_block = {
                        "number": block['section'],
                        "subtitle": block['section_subtitle'],
                    }

                metadata = {
                    "part": {
                        "name": block['category'].replace("_", " ").title(),
                        "subtitle": block['category_subtitle'],
                    },
                    "chapter": chapter_block,
                    "section": section_block,
                    "article": block['article'],
                    "paragraph": block['segment'],
                }

                if block['amendment_ratified']:
                    metadata["ratified"] = block['amendment_ratified']

                output.append({
                    # "id": block['block_id'],
                    "position": metadata,
                    "text": block['text'],
                    "flags": {
                        "is_annulled": True if block['is_annulled'] else False,
                        "is_amended": True if block['is_amended'] else False,
                        "is_superseded": True if block['is_superseded'] else False,
                    },
                    "changes": json.loads(block['amendments']) if block['amendments'] else None,
                })

        return output

    def create_assistant(self):
        instructions = (
            "You are a legal analyst, and you can only answer questions about the Constitution of Massachusetts. "
            "The provided documentation will contain all the text from the 4 parts of the Constitution (preamble, part one, part two, and amendments) "
            "listed as sequential chunks of text, along with associated metadata, such as the position of the chunk in the original document "
            "(chapter, section, article, and/or paragraph), as well as whether it has been annulled, amended, or superseded (and any related amendments).\n\n"
            "There are 121 amendments in total.\n\n"
            "Wherever possible, provide direct quotes when answering questions, "
            "and cite those quotes by referencing the part, chapter, section, article, and paragraph; for example:\n\n"
            "The department of legislation shall be formed by two branches, a Senate and House of Representatives: each of which shall have a negative on the other.\n"
            "(Part Two, Chapter 1, Section 1, Article 1, Paragraph 1)\n\n"
            "Please consider annulments, amendments, and superseding text when answering specific questions."
        )

        assistant = client.beta.assistants.create(
            name="Massachusetts Constitution Analyst",
            instructions=instructions,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )

        if assistant:
            sql = """UPDATE assistants SET is_primary = 0;"""
            self.db.mutate(sql)

            sql = """INSERT INTO assistants (assistant_id, instructions, model, is_primary)
                     VALUES (%s, %s, %s, 1);"""

            self.db.insert(sql, (assistant.id, instructions, assistant.model))

    def create_vector_store(self):
        local_file = "ma_constitution.json"
        content = self.compose_language()

        with open(local_file, 'w') as json_file:
            json.dump(content, json_file, indent=4, sort_keys=True)

        if os.path.exists(local_file):
            vector_store = client.beta.vector_stores.create(name="MA Constitution")
            if vector_store:
                sql = """UPDATE vector_stores 
                         SET is_primary = 0;"""

                self.db.mutate(sql)

                sql = """INSERT INTO vector_stores (vector_store_id, name, is_primary)
                         VALUES (%s, %s, 1);"""

                self.db.insert(sql, (vector_store.id, vector_store.name))

                client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id,
                    files=[open(local_file, "rb")],
                )

                os.path.remove(local_file)

    def join_vector_assistant(self):
        vector_store_id = self.get_primary_assistant()
        assistant_id = self.get_primary_vector_store()

        if vector_store_id and assistant_id:
            client.beta.assistants.update(
                assistant_id=assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            )

    def compare_bill(self, bill_url, redo=False):
        if not redo:
            sql = """SELECT response 
                     FROM bill_comparisons
                     WHERE bill_url = %s;"""

            known_response = self.db.select_all(sql, (bill_url,))
            if known_response:
                return known_response[0]['response']

        assistant_id = self.get_primary_vector_store()

        local_file = self.download_pdf(bill_url)
        if local_file:
            sql = """SELECT file_id 
                     FROM assistant_files 
                     WHERE filename = %s;"""

            file_id = self.db.select_one(sql, (local_file,))
            if file_id:
                file_id = file_id['file_id']

            else:
                message_file = client.files.create(
                    file=open(local_file, "rb"),
                    purpose="assistants",
                )

                if message_file:
                    file_id = message_file.id

                    sql = """INSERT INTO assistant_files (filename, file_id)
                             VALUES (%s, %s);"""

                    self.db.insert(sql, (local_file, file_id))

            if os.path.exists(local_file):
                os.remove(local_file)

            if file_id:
                file_data = client.files.retrieve(file_id)
                if file_data and file_data.bytes > 0:
                    thread = client.beta.threads.create(
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    "Given the attached bill, please determine if the text of the bill is constitutional; and if not, why is it not?\n\n"
                                    "Please provide your response in 4 sections: \n"
                                    "1. Bill Summary, which will summarize what the bill aims to do.\n"
                                    "2. Relevant Constitutional Provisions, which will be a list of citations for which part, chapter, section, and/or article of the constitution is relevant to the text of this bill.\n"
                                    "3. Analysis of the Bill, which explains how this bill conforms or does not conform to the relevant constitutional provisions listed.\n"
                                    "4. Constitutionality Conclusion, which summarizes whether or not the bill is constitutional, and why."
                                ),
                                "attachments": [
                                    {
                                        "file_id": file_id,
                                        "tools": [
                                            {
                                                "type": "file_search",
                                            }
                                        ]
                                    }
                                ],
                            }
                        ]
                    )

                    run = client.beta.threads.runs.create_and_poll(
                        thread_id=thread.id,
                        assistant_id=assistant_id,
                    )

                    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
                    message_content = messages[0].content[0].text
                    annotations = message_content.annotations
                    for index, annotation in enumerate(annotations):
                        message_content.value = message_content.value.replace(annotation.text, "")

                    response = message_content.value
                    if response:
                        sql = """INSERT INTO bill_comparisons (bill_url, response)
                                 VALUES (%s, %s)
                                 ON DUPLICATE KEY UPDATE 
                                    response = VALUES(response);"""

                        self.db.insert(sql, (bill_url, response))

                        return response