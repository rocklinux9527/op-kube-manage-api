from fastapi import FastAPI, HTTPException
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import ldap_salted_sha1

security = HTTPBearer()
JWT_SECRET_KEY = 'op-kube-manager-api-jwt'  # JWT 密钥
JWT_ALGORITHM = 'HS256'  # JWT 加密算法
JWT_EXPIRATION_TIME_MINUTES = 30  # JWT 过期时间，单位为分钟



