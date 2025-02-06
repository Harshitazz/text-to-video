# generate script from topic
from langchain_groq import ChatGroq
import json
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize the ChatGroq model
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=groq_api_key,
    temperature=0,
)


def generate_script(topic,language='Hindi',content_type="News"):
    prompt = {
        "Storytelling" :f"""
        Create a YouTube Shorts script that tells a captivating short story related to the user's requested topic. 
        The story should be concise, engaging, and fit within 50 seconds (around 140 words). 
        The script should be written in **{language}**.
        Output the script in a JSON format with the key 'script'. Here's an example of how the script might look for the topic 'inventions':

        Example output:
        {{
          "script": "The story of how bubble wrap was invented:\nIn 1957, two engineers, Alfred Fielding and Marc Chavannes, were trying to create textured wallpaper. They sealed two shower curtains together, trapping air bubbles in between. The wallpaper idea flopped, but they noticed the material's cushioning properties. Years later, IBM launched its first computers, and the engineers pitched bubble wrap as packaging material. It was a hit! Today, bubble wrap protects millions of products and even helps reduce stress with its satisfying pop. Who knew a failed wallpaper would become such a global success?"
        }}
    
        Keep it **brief, highly interesting, and unique**.
    
        Strictly output the script in a **JSON format** like below, and **only provide a parsable JSON object** with the key 'script'.
    
        # Output
        {{"script": "Here is the script ..."}}
    
        The topic is: {topic}
        """
        ,

        "Interesting-Facts":
            f"""You are a seasoned content writer for a YouTube Shorts channel, specializing in facts videos. 
        Your facts shorts are concise, each lasting less than 50 seconds (approximately 140 words). 
        The script should be written in **{language}**.
        They are incredibly engaging and original. When a user requests a specific type of facts short, you will create it.

        For instance, if the user asks for:
        Weird facts
        You would produce content like this:

        Weird facts you don't know:
        - Bananas are berries, but strawberries aren't.
        - A single cloud can weigh over a million pounds.
        - There's a species of jellyfish that is biologically immortal.
        - Honey never spoils; archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible.
        - The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.
        - Octopuses have three hearts and blue blood.

        You are now tasked with creating the best short script based on the user's requested type of 'facts'.

        Keep it brief, highly interesting, and unique.

        Stictly output the script in a JSON format like below, and only provide a parsable JSON object with the key 'script'.

        # Output
        {{"script": "Here is the script ..."}}
        The topic is: {topic}
        """
        ,

        "News": f"""
            Create a **news-style headlines** for YouTube Shorts about '{topic}'.
            - The script should be **informative and to the point**.
            - Start with a **strong headline** and **true incidents**  (e.g., "Breaking News: ...").
            - Cover the **most important details in 50 seconds (~140 words)**.
            - Use a **professional yet engaging tone**.
            - Write in **{language}**.
            - **Format:** Provide only a valid JSON response like: {{"script": "Your script here"}}
            """
    }
    selected_prompt = prompt.get(content_type, prompt["News"])
    # Invoke the ChatGroq model
    response = llm.invoke(
        selected_prompt
    )

    # Extract and return the script from the JSON response
    try:
        script = json.loads(response.content)["script"]
    except Exception as e:
        json_start_index = response.find('{')
        json_end_index = response.rfind('}')
        print(response)
        response = response[json_start_index:json_end_index + 1]
        script = json.loads(response)["script"]

    return script
