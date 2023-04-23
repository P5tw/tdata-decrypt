import hashlib

import tgcrypto

LocalEncryptNoPwdIterCount = 4
LocalEncryptIterCount = 400


class CryptoException(Exception):
    pass


def create_local_key(passcode, salt):
    if passcode:
        iterations = LocalEncryptNoPwdIterCount
    else:
        iterations = LocalEncryptIterCount

    return hashlib.pbkdf2_hmac('sha1', passcode, salt, iterations, 256)


def decrypt_local(encrypted_msg, local_key):
    msg_key, encrypted_data = encrypted_msg[:16], encrypted_msg[16:]

    decrypted = aes_decrypt_local(encrypted_data, msg_key, local_key)

    if hashlib.sha1(decrypted).digest() != msg_key:
        raise CryptoException('bad decrypt key, data not decrypted - incorrect password')

    return decrypted

def aes_decrypt_local(encrypted_data, msg_key, local_key):
    aes_key, aes_iv = prepare_aes_old_mtp(local_key, msg_key)
    return tgcrypto.ige256_decrypt(encrypted_data, aes_key, aes_iv)


def prepare_aes_old_mtp(local_key, msg_key, send=False):
    x = 0 if send else 8

    def key_pos(pos, size):
        return local_key[pos:pos + size]

    dataA = msg_key + key_pos(x, 32)
    dataB = key_pos(x + 32, 16) + msg_key + key_pos(x + 48, 16)
    dataC = key_pos(x + 64, 32) + msg_key
    dataD = msg_key + key_pos(x + 96, 32)

    sha1A = hashlib.sha1(dataA).digest()
    sha1B = hashlib.sha1(dataB).digest()
    sha1C = hashlib.sha1(dataC).digest()
    sha1D = hashlib.sha1(dataD).digest()

    key = sha1A[:8] + sha1B[8:20] + sha1C[4:16]
    iv = sha1A[8:20] + sha1B[:8] + sha1C[16:20] + sha1D[:8]

    return key, iv
