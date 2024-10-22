import hashlib
import tgcrypto

LocalEncryptNoPwdIterCount = 4
LocalEncryptIterCount = 400
KStrongIterationsCount = 100000

class CryptoException(Exception):
    pass


def create_local_key(passcode: bytes, salt: bytes) -> bytes:
    iterations = 1
    if passcode:
        iterations = KStrongIterationsCount

    password = hashlib.sha512(salt + passcode + salt).digest()

    return hashlib.pbkdf2_hmac('sha512', password, salt, iterations, 256)


def create_legacy_local_key(passcode: bytes, salt: bytes) -> bytes:
    iterations = LocalEncryptNoPwdIterCount
    if passcode:
        iterations = LocalEncryptIterCount

    return hashlib.pbkdf2_hmac('sha1', passcode, salt, iterations, 256)


def decrypt_local(data, local_key):
    key, data = data[:16], data[16:]

    decrypted = aes_decrypt_local(data, key, local_key)

    if hashlib.sha1(decrypted).digest()[:16] != key:
        raise CryptoException('bad decrypt key, data not decrypted - incorrect password')

    length = int.from_bytes(decrypted[:4], 'little')
    if length > len(decrypted):
        raise CryptoException(f'corrupted data. wrong length: {length}')

    return decrypted[4:length]


def aes_decrypt_local(data, data_key, local_key):
    aes_key, aes_iv = prepare_aes_old_mtp(data_key, local_key)

    return tgcrypto.ige256_decrypt(data, aes_key, aes_iv)


# https://github.com/telegramdesktop/tdesktop/blob/335095a332607c41a8d20b47e61f5bbd66366d4b/Telegram/SourceFiles/mtproto/mtproto_auth_key.cpp#L42
def prepare_aes_old_mtp(data_key, local_key, send=False):
    x = 0 if send else 8

    def key_pos(pos, size):
        return local_key[pos:pos + size]

    dataA = data_key + key_pos(x, 32)
    dataB = key_pos(x + 32, 16) + data_key + key_pos(x + 48, 16)
    dataC = key_pos(x + 64, 32) + data_key
    dataD = data_key + key_pos(x + 96, 32)

    sha1A = hashlib.sha1(dataA).digest()
    sha1B = hashlib.sha1(dataB).digest()
    sha1C = hashlib.sha1(dataC).digest()
    sha1D = hashlib.sha1(dataD).digest()

    key = sha1A[:8] + sha1B[8:20] + sha1C[4:16]
    iv = sha1A[8:20] + sha1B[:8] + sha1C[16:20] + sha1D[:8]

    return key, iv
