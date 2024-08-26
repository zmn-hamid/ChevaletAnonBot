def fetch_text(file_name):
    with open(f"Texts/{file_name}.txt", encoding="utf-8") as f:
        return f.read().strip()
