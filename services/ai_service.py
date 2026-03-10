import google.generativeai as genai
import json
import re

def _get_client(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def clean_json(text: str) -> str:
    """Remove markdown code fences from AI JSON responses"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    return text.strip()

def generate_explanation(api_key: str, concept_id: str, teaching_style: str) -> str:
    model = _get_client(api_key)
    
    style_instructions = {
        "example_heavy": "Use many real-world examples. Show at least 4-5 examples. Lead with examples before theory. Use banking/exam context examples.",
        "step_by_step": "Break down everything into numbered steps. Build understanding gradually. Each step should lead to the next.",
        "definition_first": "Start with a clear, precise definition. Then explain rules. Then give examples. Be formal and thorough.",
        "question_based": "Teach using questions and answers. Ask questions the student should be thinking, then answer them. Use a Socratic approach.",
    }
    
    style_text = style_instructions.get(teaching_style, style_instructions["example_heavy"])
    
    prompt = f"""You are an expert English teacher helping Indian students prepare for banking exams like IBPS, SBI, RBI.

Teach the concept: "{concept_id}"

Teaching approach: {style_text}

Requirements:
- Keep language simple and clear
- Include banking exam relevant examples
- Mention common mistakes students make
- Keep it practical and exam-focused
- Maximum 400 words
- Use plain text only (no markdown, no asterisks, no special symbols)

Start teaching directly without any introduction like "Sure!" or "Of course!"."""

    response = model.generate_content(prompt)
    return response.text

def generate_exercises(api_key: str, concept_id: str, difficulty: str) -> list:
    model = _get_client(api_key)
    
    prompt = f"""You are an English exam expert creating exercises for banking exam aspirants.

Create 5 practice exercises for concept: "{concept_id}"
Difficulty level: {difficulty}

Return ONLY a JSON array (no markdown, no explanation, just JSON):
[
  {{
    "question": "Fill the blank or identify: ...",
    "options": ["option A", "option B", "option C", "option D"],
    "correct_answer": "option A",
    "activity_type": "fill_blank",
    "explanation": "Brief explanation of why this answer is correct"
  }}
]

Rules:
- Mix question types: fill in blank, identify the correct sentence, choose correct word
- Use banking/exam context in sentences
- Make options plausible (not obviously wrong)
- Explanation should be 1-2 sentences
- Return ONLY the JSON array"""

    response = model.generate_content(prompt)
    text = clean_json(response.text)
    try:
        exercises = json.loads(text)
        return exercises if isinstance(exercises, list) else []
    except json.JSONDecodeError:
        # Try to extract JSON array
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return []

def generate_revision_questions(api_key: str, concept_id: str) -> list:
    model = _get_client(api_key)
    
    prompt = f"""Create 4 quick revision questions for: "{concept_id}"

These are for spaced repetition review for banking exam preparation.

Return ONLY a JSON array:
[
  {{
    "question": "Short, clear question",
    "options": ["A", "B", "C"],
    "correct_answer": "A",
    "quick_tip": "One sentence memory tip"
  }}
]

Return ONLY the JSON array, nothing else."""

    response = model.generate_content(prompt)
    text = clean_json(response.text)
    try:
        questions = json.loads(text)
        return questions if isinstance(questions, list) else []
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return []
