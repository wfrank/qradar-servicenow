try:
    import Crypto.Random as Random
    import Crypto.Cipher.AES as AES

    class CryptoUtils:
        def __init__(self):
            """" Simple AES Wrapper """""

        @staticmethod
        def gen_key():
            return Random.new().read(32).encode('base64')

        def encrypt(self, plain_text, key):
            key = key.decode('base64')
            plain_text = self._pad(plain_text)
            initial = Random.new().read(AES.block_size)
            enc = AES.new(key, AES.MODE_CBC, initial)
            return (initial + enc.encrypt(plain_text)).encode('base64')

        def decrypt(self, encrypted_text, key):
            key = key.decode('base64')
            encrypted_text = encrypted_text.decode('base64')
            if len(encrypted_text) <= AES.block_size:
                return None
            initial = encrypted_text[:AES.block_size]
            encrypted_text = encrypted_text[AES.block_size:]
            enc = AES.new(key, AES.MODE_CBC, initial)
            return self._unpad(enc.decrypt(encrypted_text))

        def _pad(self, input_string):
            # PKCS5 padding
            return input_string + (16 - len(input_string) % 16) * chr(16 - len(input_string) % 16)

        def _unpad(self, input_string):
            # PKCS5 unpadding
            return input_string[0:-ord(input_string[-1])]

except ImportError:

    class CryptoUtils:

        @staticmethod
        def gen_key():
            return ""

        def encrypt(self, plain_text, key):
            return plain_text

        def decrypt(self, encrypted_text, key):
            return encrypted_text
