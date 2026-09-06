"""站点资料 / 关于我 schema"""
from pydantic import Field

from app.schemas.common import ORMModel


class ProfileOut(ORMModel):
    id: int = 1
    nickname: str = "bluemoon"
    avatar: str | None = None
    bio: str | None = None
    content: str | None = None
    location: str | None = None
    email: str | None = None
    website: str | None = None
    github: str | None = None
    wechat: str | None = None
    qq: str | None = None


class ProfileIn(ORMModel):
    nickname: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=500)
    content: str | None = None
    location: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=120)
    website: str | None = Field(default=None, max_length=200)
    github: str | None = Field(default=None, max_length=200)
    wechat: str | None = Field(default=None, max_length=100)
    qq: str | None = Field(default=None, max_length=50)


class SiteInfoOut(ORMModel):
    title: str
    subtitle: str
    description: str
    author: str
    icp: str = ""
    post_count: int = 0
    category_count: int = 0
    total_views: int = 0
