import os
from pathlib import Path
from dotenv import set_key, load_dotenv
from rubpy import Client as RubikaClient

ENV_FILE = ".env"
SESSION = "rubsession"
SESSION_FILE = "rubika.session"


def ask(msg):
    return input(msg + " ").strip()


def create_new_session():
    print("\n=== Creating new Rubika session ===\n")

    phone = ask("Enter your phone number (09...):")
    if not phone.startswith("09"):
        print("❌ Invalid phone number")
        return None

    client = RubikaClient(name=SESSION)

    print("Sending verification code...")
    try:
        sent_code = client.send_code(phone)
    except Exception as e:
        print("❌ Failed to send code:", e)
        return None

    code = ask("Enter verification code:")

    try:
        client.sign_in(phone, sent_code, code)
    except Exception as e:
        print("❌ Login failed:", e)
        return None

    client.save_session(SESSION_FILE)
    client.disconnect()

    print(f"✔ Session saved as {SESSION_FILE}")

    set_key(ENV_FILE, "RUBIKA_SESSION", SESSION_FILE)

    return SESSION_FILE


def choose_session():
    exists = Path(SESSION_FILE).exists()

    if exists:
        print(f"\nExisting Rubika session found: {SESSION_FILE}\n")
        choice = ask("Use this session? (y/n):")

        if choice.lower().startswith("y"):
            print("✔ Using existing session")
            set_key(ENV_FILE, "RUBIKA_SESSION", SESSION_FILE)
            return SESSION_FILE

        print("Creating new session...")
        return create_new_session()

    else:
        print("No session found → Creating new session")
        return create_new_session()


def main():
    print("=== Rubika Session Setup ===")

    if not os.path.exists(ENV_FILE):
        open(ENV_FILE, "w").close()

    load_dotenv(ENV_FILE)

    session = choose_session()

    if not session:
        print("❌ Session setup failed!")
        exit(1)

    print("✔ Rubika session setup completed successfully.")


if __name__ == "__main__":
    main()
