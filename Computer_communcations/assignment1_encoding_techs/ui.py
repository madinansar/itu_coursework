
def ask_bits(prompt="Enter bit string (only 0/1): "):
    while True:
        s = input(prompt).strip()
        if s == "":
            print("Input cannot be empty. Please enter a bit string like 1011001.")
            continue
        if all(ch in "01" for ch in s):
            return s
        print("Invalid input. Please enter only 0 and 1 (example: 1011001).")


def ask_int(prompt="Enter an integer: "):
    while True:
        s = input(prompt).strip()
        if s == "":
            print("Input cannot be empty. Please enter an integer.")
            continue
        try:
            return int(s)
        except ValueError:
            print("Invalid input. Please enter a valid integer (example: 100).")


def ask_float(prompt="Enter a number: "):
    while True:
        s = input(prompt).strip()
        if s == "":
            print("Input cannot be empty. Please enter a number.")
            continue
        try:
            return float(s)
        except ValueError:
            print("Invalid input. Please enter a valid number (example: 3.5).")


def ask_choice(title, options):
    """
    options example:
      [("1","NRZ-L"), ("2","NRZ-I")]
    Returns the chosen key as a string, e.g. "1".
    """
    while True:
        print("\n" + title)
        for k, label in options:
            print(f"  {k}) {label}")

        choice = input("Choose: ").strip()
        valid_keys = {k for k, _ in options}

        if choice in valid_keys:
            return choice

        print(f"Invalid choice. Please enter one of: {', '.join(sorted(valid_keys))}.")