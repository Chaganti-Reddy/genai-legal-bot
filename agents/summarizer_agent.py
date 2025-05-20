from typing import List
import subprocess
import os
import json

class SummarizerAgent:

    def __init__(self, model="ollama", gemini_key=None, openai_key=None, groq_key=None, model_name=None):
        self.model = model.lower()
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.groq_key = groq_key
        self.model_name = model_name

    def summarize(self, chunks: List[str], context: str = "", user_query: str = "") -> str:
        combined_text = "\n".join(chunks)
        prompt = (
            f"You are a legal assistant. A user asked the following question:\n\n"
            f"❓ {user_query}\n\n"
            "Now summarize ONLY the legal information in the provided text that answers this question.\n"
            "- Do NOT include your reasoning or internal thoughts.\n"
            "- Do NOT ask what the user wants — they have already asked.\n"
            "- Format the output in bullet points or numbered steps.\n"
            "- Keep it concise, legally accurate, and based ONLY on the provided legal text.\n\n"
            f"[Legal Text]\n{combined_text.strip()}\n\n"
            "End your response with: 'Would you like further explanation on any point above?'"
        )

        if self.model == "ollama":
            result = subprocess.run(
                ["ollama", "run", self.model_name or "llama3"],
                input=prompt.encode("utf-8"),
                capture_output=True
            )
            output = result.stdout.decode("utf-8").strip() if result.returncode == 0 else "[Error: Ollama failed]"

        elif self.model == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(self.model_name or "models/gemini-1.5-pro-latest")
                response = model.generate_content(prompt)
                output = response.text.strip()
            except Exception as e:
                output = f"[Gemini Error: {str(e)}]"

        elif self.model == "openai":
            try:
                import openai
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model=self.model_name or "gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a legal assistant that summarizes legal content without adding outside knowledge."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=600
                )
                output = response['choices'][0]['message']['content'].strip()
            except Exception as e:
                output = f"[OpenAI Error: {str(e)}]"

        elif self.model == "groq":
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a legal assistant that summarizes legal content without adding outside knowledge."},
                        {"role": "user", "content": prompt}
                    ]
                )
                output = response.choices[0].message.content.strip()
            except Exception as e:
                output = f"[Groq Error: {str(e)}]"

        else:
            output = "[Error: Unsupported model selected]"

        return output

