import os
import math
from datetime import date, timedelta

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(
    page_title="StudyGenie - AI Student Assistant",
    page_icon="🎓",
    layout="wide"
)

def get_openai_client():
    """
    Returns an OpenAI client if the package is installed
    and OPENAI_API_KEY is available.
    """
    api_key = os.getenv("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")
    if OpenAI is not None and api_key:
        return OpenAI(api_key=api_key)
    return None


def clean_text(text: str) -> str:
    """Basic cleanup for uploaded text."""
    return " ".join(text.split()).strip()


def extract_text_from_uploaded_file(uploaded_file):
    """
    Reads text from txt / md / csv files.
    PDF and DOCX are not included 
    """
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:
        raw = uploaded_file.read()

        if file_name.endswith((".txt", ".md", ".csv")):
            return raw.decode("utf-8", errors="ignore")

        return ""
    except Exception:
        return ""


def fallback_summary(text: str) -> str:
    """
    Rule based summary when no API key is available.
    """
    sentences = text.replace("\n", " ").split(".")
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return "No content found to summarize."

    first_sentences = sentences[:5]
    summary = ". ".join(first_sentences)
    if not summary.endswith("."):
        summary += "."

    return (
        "Summary (basic mode):\n\n"
        f"{summary}\n\n"
        "Tip: Add an OpenAI API key to get a smarter AI summary."
    )


def fallback_quiz(text: str, num_questions: int = 5) -> str:
    """
    Rule-based quiz fallback.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) < num_questions:
        lines = text.split(".")
        lines = [line.strip() for line in lines if line.strip()]

    if not lines:
        return "Not enough text to create quiz questions."

    output = []
    for i in range(min(num_questions, len(lines))):
        chunk = lines[i][:150]
        output.append(
            f"{i+1}. What is the main idea of this statement?\n"
            f"   \"{chunk}\"\n"
            f"   Answer: Students should explain the key concept in their own words.\n"
        )

    return "\n".join(output)


def create_study_plan(topics_text: str, exam_date: date, hours_per_day: float):
    """
    Creates a simple study plan based on the topics and exam date.
    """
    today = date.today()
    days_left = (exam_date - today).days

    if days_left < 1:
        return ["Your exam date must be at least tomorrow."]

    topics = [t.strip() for t in topics_text.split("\n") if t.strip()]
    if not topics:
        topics = ["Review all uploaded notes", "Practice problems", "Final revision"]

    total_topics = len(topics)
    topics_per_day = max(1, math.ceil(total_topics / days_left))

    plan = []
    topic_index = 0

    for day in range(days_left):
        current_day = today + timedelta(days=day)
        todays_topics = topics[topic_index: topic_index + topics_per_day]

        if not todays_topics:
            todays_topics = ["Review previous topics", "Practice active recall"]

        plan.append(
            f"{current_day.strftime('%Y-%m-%d')}: "
            f"Study for {hours_per_day} hour(s) -> " + ", ".join(todays_topics)
        )

        topic_index += topics_per_day

    return plan


def ask_ai(prompt: str, system_message: str = "You are a helpful academic assistant.") -> str:
    """
    Sends a prompt to OpenAI if available.
    Otherwise returns None.
    """
    client = get_openai_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling AI API: {e}"


def ai_summary(text: str) -> str:
    prompt = f"""
Summarize the following student notes in a clear and simple way.

Instructions:
- Use bullet points
- Keep it concise
- Highlight key ideas, formulas, and definitions
- End with 3 important takeaways

Notes:
{text[:12000]}
"""
    result = ask_ai(prompt, system_message="You are an expert tutor who summarizes notes clearly.")
    return result if result else fallback_summary(text)


def ai_quiz(text: str, num_questions: int = 5) -> str:
    prompt = f"""
Create {num_questions} quiz questions from these notes.

Instructions:
- Include a mix of short answer and multiple choice questions
- Provide the answers
- Make questions university level but clear
- Format neatly

Notes:
{text[:12000]}
"""
    result = ask_ai(prompt, system_message="You are a university quiz generator.")
    return result if result else fallback_quiz(text, num_questions)


def ai_chat_with_notes(text: str, question: str) -> str:
    prompt = f"""
You are answering questions only using the student's notes below.

Student Notes:
{text[:12000]}

Question:
{question}

Instructions:
- Answer clearly
- If the notes do not contain enough information, say that directly
- Keep the answer student friendly
"""
    result = ask_ai(prompt, system_message="You are a helpful study assistant.")
    if result:
        return result

    return (
        "Basic mode answer:\n\n"
        "I cannot deeply analyze the notes without an API key, but based on the uploaded text, "
        "please review the related section manually."
    )

st.title("🎓🏆 StudyGenie")
st.subheader("Study Smart. Stress Less. Graduate Strong.")

st.markdown(
    """

🎓 Welcome to StudyGenie 🎓

An AI powered platform built to support your university journey. Stay organized, learn efficiently, and succeed with StudyGenie designed just for you.

Meet your all-in-one AI study assistant 
• ⚡ Instantly summarize your notes
• 🎯 Turn content into smart quizzes
• 🗂️ Create customized study schedules
       • 🤖 Ask anything  get answers from your own notes

"""
)

with st.sidebar:
    st.header("⚙️ Setup")
    st.write("To enable real AI features, set your OpenAI API key as an environment variable:")
    st.code("OPENAI_API_KEY=your_api_key_here")
    st.write("Without an API key, the app still works in basic fallback mode.")

    st.header("📁 Supported Files")
    st.write("- .txt")
    st.write("- .md")
    st.write("- .csv")

    st.write(
        "During your demo, show:\n"
        "1. Upload notes\n"
        "2. Click Summarize\n"
        "3. Generate quiz\n"
        "4. Create study plan"
    )


uploaded_file = st.file_uploader(
    "Upload your notes",
    type=["txt", "md", "csv"]
)

notes_text = ""
if uploaded_file:
    notes_text = extract_text_from_uploaded_file(uploaded_file)
    notes_text = clean_text(notes_text)

    if notes_text:
        st.success("File uploaded successfully.")
    else:
        st.warning("Could not read text from that file. Please upload a .txt, .md, or .csv file.")


tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Summarizer",
    "❓ Quiz Generator",
    "📅 Study Planner",
    "💬 Chat with Notes"
])



# TAB 1 - SUMMARIZER

with tab1:
    st.header("Notes Summarizer")

    if st.button("Generate Summary"):
        if not notes_text:
            st.error("Please upload notes first.")
        else:
            with st.spinner("Generating summary..."):
                summary = ai_summary(notes_text)
            st.text_area("Summary Output", summary, height=350)



# TAB 2 - QUIZ
#
with tab2:
    st.header("Quiz Generator")

    num_questions = st.slider("Number of questions", 3, 10, 5)

    if st.button("Generate Quiz"):
        if not notes_text:
            st.error("Please upload notes first.")
        else:
            with st.spinner("Generating quiz..."):
                quiz = ai_quiz(notes_text, num_questions)
            st.text_area("Quiz Output", quiz, height=350)


# TAB 3 - STUDY PLANNER
# -----------------------------
with tab3:
    st.header("Study Planner")

    st.write("Enter your topics below, one topic per line.")
    topics_input = st.text_area(
        "Topics",
        placeholder="Chapter 1\nChapter 2\nDerivatives\nIntegration\nFinal review",
        height=180
    )

    exam_date = st.date_input("Exam Date", min_value=date.today() + timedelta(days=1))
    hours_per_day = st.number_input("Study hours per day", min_value=0.5, max_value=12.0, value=2.0, step=0.5)

    if st.button("Create Study Plan"):
        plan = create_study_plan(topics_input, exam_date, hours_per_day)
        st.subheader("Your Study Plan")
        for item in plan:
            st.write(f"- {item}")



# TAB 4 - CHAT

with tab4:
    st.header("Chat with Your Notes")

    question = st.text_input("Ask a question about your notes")

    if st.button("Ask"):
        if not notes_text:
            st.error("Please upload notes first.")
        elif not question.strip():
            st.error("Please enter a question.")
        else:
            with st.spinner("Thinking..."):
                answer = ai_chat_with_notes(notes_text, question)
            st.text_area("Answer", answer, height=250)



# FOOTER

st.markdown("---")
st.markdown(
    """ Study Smart. Stress Less. Graduate Strong.
© 2026 StudyGenie™ · Built for the future of learning """
)
