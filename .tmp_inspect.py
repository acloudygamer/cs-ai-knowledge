import io
raw = io.open(r"test.md", encoding="utf-8", newline="").read()
print("len:", len(raw))
print("crlf:", raw.count("\r\n"), "crcrlf:", raw.count("\r\r\n"), "lf-only:", raw.count("\n") - raw.count("\r\n"))
print("first 300 repr:")
print(repr(raw[:300]))
