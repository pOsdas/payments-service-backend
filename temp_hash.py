from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


print("admin12345 ->", hash_password("admin12345"))
print("user12345  ->", hash_password("user12345"))