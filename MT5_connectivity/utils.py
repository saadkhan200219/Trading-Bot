import pandas as pd
def save_to_excel(user_data):
    df = pd.DataFrame(user_data)
    df.to_excel("user_data.xlsx", index=False)

def load_from_excel():
    try:
        df = pd.read_excel("user_data.xlsx")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["username", "password"])
    return df

def is_username_available(username, user_data):
    return username not in user_data["username"].values

def is_login_valid(username, password, user_data):
    if username in user_data["username"].values:
        stored_password = user_data[user_data["username"] == username]["password"].values
        if len(stored_password) > 0:
            return str(stored_password[0]) == password
    return False