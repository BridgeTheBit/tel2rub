import re
from pathlib import Path
from rubpy import Client as RubikaClient


SESSION = "rubika_session"


def normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("09"):
        phone = "98" + phone[1:]

    if not phone.startswith("98"):
        raise ValueError("Phone must be in format 989xxxxxxxxx")

    return phone


def delete_session(session_name: str):
    for path in [
        Path(session_name),
        Path(f"{session_name}.session"),
        Path(f"{session_name}.sqlite"),
    ]:
        if path.exists():
            path.unlink()


def has_session(session_name: str) -> bool:
    return any(
        Path(p).exists()
        for p in [
            session_name,
            f"{session_name}.session",
            f"{session_name}.sqlite",
        ]
    )


def main():
    print("=== Rubika Session Installer ===\n")

    if has_session(SESSION):
        print("⚠️ Session already exists.")
        choice = input("Do you want to recreate it? (y/n): ").lower()

        if choice != "y":
            print("Exit.")
            return

        delete_session(SESSION)
        print("Old session deleted.\n")

    try:
        phone = input("Enter phone (989xxxxxxxxx): ")
        phone = normalize_phone(phone)

    except Exception as e:
        print("Invalid phone:", e)
        return

    client = RubikaClient(name=SESSION)

    try:
        print("\n📲 Requesting verification code...")
        client.start(phone_number=phone)
        print("\n✅ Login successful!")
        print("Session saved as:", SESSION)

    except Exception as e:
        print("\n❌ Login failed!")
        print("Error:", e)

    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()
