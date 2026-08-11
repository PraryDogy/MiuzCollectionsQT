def test(mf, path):
    text = f"test {mf} {path}"
    return text


cmd = lambda x, y: test(x, y)
for i in range(0, 10):
    text = cmd(i, i)
    print(text)