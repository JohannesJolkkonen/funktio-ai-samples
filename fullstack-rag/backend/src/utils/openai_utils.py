from openai import OpenAI, AsyncOpenAI
from string import Template
from decouple import config 

client = OpenAI(api_key=config("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=config("OPENAI_API_KEY"))


prompt_template = Template("""
Answer the question based on the context, in a concise manner, in markdown and using bullet points where applicable.

Context: $context
Question: $question
Answer:
""")


def get_embedding(text: str):
    return client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
    ).data[0].embedding


async def stream_completion(question: str, docs: dict):
    context = "\n".join([doc.get("page_content") for doc in docs])
    prompt = prompt_template.substitute(context=context, question=question)
    response = await async_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
        ],
        stream=True
    )
    async for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content
