import re
def is_password_strong(password):
    
    min_length = 8
    has_upper = re.search(r'[A-Z]', password)
    has_lower = re.search(r'[a-z]', password)
    has_digit = re.search(r'\d', password)
    has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    if (has_upper and has_lower and has_digit and has_special and len(password) >= min_length):
        return True
    else:
        return False