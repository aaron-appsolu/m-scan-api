from bson import ObjectId
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.mongo import users
from app.routers import main
from app.settings import settings
import jwt

origins = [
    "https://m-scan-v2.made4it.com",
    "http://localhost:4200"
]

# mypy ./app/main.py
# bandit?

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main.router)


@app.middleware("http")
async def access(request: Request, call_next):
    if request.method == 'OPTIONS':
        return await call_next(request)

    jwt_options = {'verify_signature': True}
    authorization = request.headers.get('Authorization')

    if not authorization:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={'reason': 'No Authorization Token'})

    token = authorization.split(' ')[1]
    jwt_payload = jwt.decode(token,
                             options=jwt_options,
                             verify=True,
                             key=settings.SECRET,
                             algorithms=["HS256"])
    user = users.find_one({'_id': ObjectId(jwt_payload['_id'])})

    if not user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={'reason': 'No User'})

    application = 'mscan'
    requested_application = request.query_params.get('application')
    owner = request.query_params.get('owner')

    if ((application not in user['applications'])
            or (application not in user)
            or (requested_application != application)):
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'reason': 'No access to application'})

    application_data = user[application]

    if owner and owner not in application_data.get('owner', []):
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                            content={'reason': 'No ownership of the requested data'})

    request.state.user_data = application_data
    return await call_next(request)
