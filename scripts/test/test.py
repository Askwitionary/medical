import hashlib

a = hashlib.md5("中产网".encode("utf-8")).hexdigest()
b = hashlib.md5("中隧网".encode("utf-8")).hexdigest()


