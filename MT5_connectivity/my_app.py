import streamlit as st
import pandas as pd
import yfinance as yf
from news import display_news
from pass_val import is_password_strong
from utils import *
st.markdown(
    """
    <style>
    .reportview-container {
        background: url('https://miro.medium.com/v2/resize:fit:828/format:webp/1*uvdeDKqzzz4IO_kq4WWE9A.png')
    }
    </style>
    """,
    unsafe_allow_html=True
)



def main():
    st.title("Trading Bot Login and Signup")

    user_data = load_from_excel()

    page = st.sidebar.radio("Navigation", ["Login", "Signup"])

    if page == "Signup":
        st.subheader("Create an Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Sign Up"):
            if is_username_available(username, user_data):
                if is_password_strong(password):
                    user_data = user_data._append({"username": username, "password": password}, ignore_index=True)
                    save_to_excel(user_data)
                    st.success("Account created successfully! You can now login.")
                else:
                    st.error("Password is not strong enough. Please make sure it contains at least 8 characters, including uppercase letters, lowercase letters, digits, and special characters.")
            else:
                st.error("Username already exists. Please choose another one.")

    elif page == "Login":
        st.subheader("Login to Your Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if is_login_valid(username, password, user_data):
               
                st.markdown(f"## Welcome back, {username}!")
                display_news()
            else:
                st.error("Invalid username or password. Please try again.")

if __name__ == "__main__":
    main()
