import streamlit as st
import google.generativeai as genai
import random
import re

# Function to initialize the model with API Key
def initialize_model(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-001')
    return model

# Function to generate a question
def generate_question(model,expertin):
    system_prompt = f"""
        You are an expert in {expertin} exams. Your role is to generate questions related to {expertin} for candidates appearing for the exam.
        Generate only one question at a time, followed by four options labeled A, B, C and D. Do not use any numbering.
        The options must be mutually exclusive.
        Do not ask any clarification questions. Do not engage in any chit chat. Generate questions only about {expertin} exam.
        Format the output strictly as follows:
        
        Question: <Question>
        A: <Option A>
        B: <Option B>
        C: <Option C>
        D: <Option D>
        
    """

    response = model.generate_content(system_prompt)
    return response.text

# Function to extract question and options
def parse_question_response(response_text):
    
    question_match = re.search(r"Question:\s*(.+?)\s*(?=A:)", response_text, re.DOTALL)
    a_match = re.search(r"A:\s*(.+?)\s*(?=B:)", response_text, re.DOTALL)
    b_match = re.search(r"B:\s*(.+?)\s*(?=C:)", response_text, re.DOTALL)
    c_match = re.search(r"C:\s*(.+?)\s*(?=D:)", response_text, re.DOTALL)
    d_match = re.search(r"D:\s*(.+)", response_text, re.DOTALL)

    if question_match and a_match and b_match and c_match and d_match:
        question = question_match.group(1).strip()
        options = {
            "A": a_match.group(1).strip(),
            "B": b_match.group(1).strip(),
            "C": c_match.group(1).strip(),
            "D": d_match.group(1).strip()
            }
        return question, options
    else:
        return None, None

# Function to determine the correct answer and generate explanation
def get_answer_and_explanation(model, expertin, question, options, user_answer):
    system_prompt = f"""
    You are an expert in {expertin} exams.
    Given the following question, options, and the user's chosen option(s), your task is to:
    1.  Identify the correct option(s). The correct answer can be a single answer or multiple answers.
    2.  Provide a detailed explanation for why each of the correct options is the right one.
    3.  Provide a detailed explanation for why each of the incorrect options are wrong.
    4.  Provide references/sources for the correctness/incorrectness of the options. 
    
    Question: {question}
    Options: {options}
    User's answer: {user_answer}
    
    Your output should be as follows:
    
    Correct Answer(s): <list of correct options like ['A', 'B']>
    Explanation for correct option(s): <detailed explanation and sources>
    Explanation for incorrect option(s): <detailed explanation and sources>
    """
    response = model.generate_content(system_prompt)
    return response.text

# Streamlit App
def main():
    st.set_page_config(page_title="Exam Practice - Multiple Choice QnA", page_icon=":mortar_board:")

    # Sidebar for API Key input
    with st.sidebar:
       st.header("Enter API Key")
       api_key = st.text_input("Enter your Gemini API key:", type="password")
       if api_key:
            model = initialize_model(api_key)
            st.success("API key loaded successfully!")
       else:
            model = None  # Disable functionality if API key not entered
            st.warning("Please enter an API key to continue.")
       st.header("Which Certification Exam would you like to practice for?")
       choice = st.selectbox("Select Exam", ["Google Professional Machine Learning Engineer",
                                              "AWS Solution Architect Associate", 
                                              "Microsoft Azure Data Fundamentals"])
       st.write(f"You selected {choice}")

    st.title(f"{choice} Exam Practice")

    # Initialize session state
    if 'question' not in st.session_state:
        st.session_state.question = None
    if 'options' not in st.session_state:
        st.session_state.options = None
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = []
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'answer_explanation' not in st.session_state:
        st.session_state.answer_explanation = None

    # Generate question button
    if model and st.button("Generate Question", disabled=st.session_state.question is not None):
        response_text = generate_question(model,choice)
        question, options = parse_question_response(response_text)
        if question and options:
            st.session_state.question = question
            st.session_state.options = options
            st.session_state.user_answer = []
            st.session_state.show_answer = False
            st.session_state.answer_explanation = None
        else:
            st.error("Failed to parse the question. Please try again.")

    # Display question if available
    if st.session_state.question:
      st.subheader("Question:")
      st.write(st.session_state.question)
      st.subheader("Options:")
      
      # Create columns for checkboxes
      cols = st.columns(2)
      
      with cols[0]:
          option_a_selected = st.checkbox(f"A: {st.session_state.options['A']}", key="option_a")
      with cols[1]:
          option_b_selected = st.checkbox(f"B: {st.session_state.options['B']}", key="option_b")
      with cols[0]:
          option_c_selected = st.checkbox(f"C: {st.session_state.options['C']}", key="option_c")
      with cols[1]:
          option_d_selected = st.checkbox(f"D: {st.session_state.options['D']}", key="option_d")
      
      # Handle user answers in a list, allows for multi-select
      user_answer = []
      if option_a_selected:
          user_answer.append('A')
      if option_b_selected:
          user_answer.append('B')
      if option_c_selected:
          user_answer.append('C')
      if option_d_selected:
          user_answer.append('D')

      st.session_state.user_answer = user_answer

      # Submit Answer Button
      if st.button("Submit Answer", disabled=not st.session_state.user_answer):
        st.session_state.show_answer = True
        st.session_state.answer_explanation = get_answer_and_explanation(model, choice, st.session_state.question, st.session_state.options, st.session_state.user_answer)
    
    # Display answer and explanation
    if st.session_state.show_answer and st.session_state.answer_explanation:
        st.subheader("Answer and Explanation:")
        st.write(st.session_state.answer_explanation)
        st.session_state.question = None # Reset the question when we show the answer, so that user can click on generate next question button
        
if __name__ == "__main__":
    main()
