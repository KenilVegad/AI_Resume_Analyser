from groq import Groq
import json

from dotenv import load_dotenv
import os

load_dotenv()


client = Groq(
    api_key= os.getenv("GROQ_API_KEY")
)

def analyze_resume(resume_text, user_goal):

    prompt = f"""
You are a senior software engineer and hiring manager.

Evaluate the resume based on the user's goal.

User Goal:
{user_goal}

STRICT RULES:
- Extract only relevant skills
- Remove irrelevant skills
- Identify missing skills
- Generate roadmap
- Generate interview questions

Return ONLY JSON:

{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:

{resume_text}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You're a strict hiring manager."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        start = content.find("{")
        end = content.rfind("}") + 1

        return json.loads(content[start:end])

    except Exception as e:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }