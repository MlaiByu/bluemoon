"""站点资料：关于我 / 站点信息（单条记录，id 固定为 1）"""
from sqlalchemy import Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profile"
    __table_args__ = ({"comment": "站点资料表（单条）"},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, default="bluemoon", server_default="bluemoon")
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="一句话简介")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="关于我（Markdown）")
    location: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="所在地")
    email: Mapped[str | None] = mapped_column(String(120), nullable=True, comment="邮箱")
    website: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="网站")
    github: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="GitHub")
    wechat: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="微信")
    qq: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="QQ")

    def __repr__(self) -> str:
        return f"<Profile {self.nickname}>"
