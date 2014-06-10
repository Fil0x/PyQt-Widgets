escape_dict={'\a':r'\a',
           '\b':r'\b',
           '\c':r'\c',
           '\f':r'\f',
           '\n':r'\n',
           '\r':r'\r',
           '\t':r'\t',
           '\v':r'\v',
           '\'':r'\'',
           '\"':r'\"',
           '\0':r'\0',
           '\1':r'\1',
           '\2':r'\2',
           '\3':r'\3',
           '\4':r'\4',
           '\5':r'\5',
           '\6':r'\6',
           '\7':r'\7',
           '\8':r'\8',
           '\9':r'\9'}

def raw(text):
    """Returns a raw string representation of text"""
    new_string=''
    for char in text:
        try: new_string+=escape_dict[char]
        except KeyError: new_string+=char
    return new_string

def shorten_str(s, max_len, ratio=2./3):
    rc, new_s = '...', s
    if len(s) > max_len:
        s_1, s_2 = s[0:len(s)//2-1], s[len(s)//2+2:]
        diff = len(s) - max_len
        delete = 1 if diff == 1 else int(diff*ratio)
        new_s = '{}{}{}'.format(s_1[0:len(s_1)-delete], rc,
                                s_2[diff-delete:])

    return new_s
