import io
p = r"test.md"
raw = io.open(p, encoding="utf-8", newline="").read()
fixed = raw.replace("\r\r\n", "\r\n")
io.open(p, "w", encoding="utf-8", newline="").write(fixed)
chk = io.open(p, encoding="utf-8", newline="").read()
print("crcrlf after fix:", chk.count("\r\r\n"), "crlf:", chk.count("\r\n"),
      "lines:", len(chk.split("\r\n")))
