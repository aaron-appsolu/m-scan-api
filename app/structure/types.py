from pydantic import BaseModel


class StandardisedFormat(BaseModel):
    std: str = ""
    obs: str = ""
    rsp: str = ""
