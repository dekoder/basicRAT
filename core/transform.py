

def xor(text):
    crypt = []
    for i in range(len(text)):
        crypt.append(chr(ord(text[i]) ^ 93))

    return "".join(crypt)
