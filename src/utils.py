def hex_to_string(str_hex):
    if str_hex.startswith('0x'):
        str_hex = str_hex[2::]
    return ''.join(chr(int(str_hex[i:i+2], 16)) for i in range(0, len(str_hex), 2))
