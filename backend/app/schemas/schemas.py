"""请求/响应模型。

重要设计:**输入严格,输出宽松**。
- `*In` 用于写入,带完整校验(长度、范围、枚举),脏数据进不来
- `*Out` 用于读取,只约束类型不约束范围 —— 历史库里可能存着
  越界值(比如 percent=99999),读取时不能因此 500。
  这类脏数据由后台改掉即可,不该让整页崩掉。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ColorKey = Literal["pink", "yellow", "teal", "purple", "orange", "blue"]
SkillCategory = Literal["serious", "passive"]
HonorLevel = Literal["national", "provincial", "school", "other"]
ProfileKind = Literal["about", "info"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------- 内容类 ----------------


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    percent: int = Field(default=50, ge=0, le=100)
    note: str = Field(default="", max_length=120)
    category: SkillCategory = "serious"
    color: ColorKey = "teal"
    sort: int = 0


class SkillOut(ORMModel):
    id: int
    name: str
    percent: int
    note: str = ""
    category: str = "serious"
    color: str = "teal"
    sort: int = 0


class TimelineIn(BaseModel):
    emoji: str = Field(default="🚀", max_length=8)
    time_label: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=80)
    content: str = Field(default="", max_length=400)
    sort: int = 0


class TimelineOut(ORMModel):
    id: int
    emoji: str = ""
    time_label: str = ""
    title: str = ""
    content: str = ""
    sort: int = 0


class StatIn(BaseModel):
    emoji: str = Field(default="😄", max_length=8)
    number: int = 0
    unit: str = Field(default="", max_length=12)
    label: str = Field(min_length=1, max_length=60)
    sort: int = 0


class StatOut(ORMModel):
    id: int
    emoji: str = ""
    number: int = 0
    unit: str = ""
    label: str = ""
    sort: int = 0


class WorkIn(BaseModel):
    emoji: str = Field(default="🛠️", max_length=8)
    cover: ColorKey = "pink"
    title: str = Field(min_length=1, max_length=80)
    desc: str = Field(default="", max_length=400)
    pill: str = Field(default="进行中", max_length=20)
    link: str = Field(default="", max_length=300)
    sort: int = 0

    @field_validator("link")
    @classmethod
    def _check_link(cls, v: str) -> str:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("链接必须以 http:// 或 https:// 开头")
        return v


class WorkOut(ORMModel):
    id: int
    emoji: str = ""
    cover: str = "pink"
    title: str = ""
    desc: str = ""
    pill: str = ""
    link: str = ""
    sort: int = 0


class ProfileIn(BaseModel):
    kind: ProfileKind = "info"
    emoji: str = Field(default="", max_length=8)
    label: str = Field(default="", max_length=40)
    value: str = Field(default="", max_length=1000)
    sort: int = 0


class ProfileOut(ORMModel):
    id: int
    kind: str = "info"
    emoji: str = ""
    label: str = ""
    value: str = ""
    sort: int = 0


class HonorIn(BaseModel):
    emoji: str = Field(default="🏆", max_length=8)
    year: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=80)
    desc: str = Field(default="", max_length=300)
    level: HonorLevel = "school"
    sort: int = 0


class HonorOut(ORMModel):
    id: int
    emoji: str = ""
    year: str = ""
    title: str = ""
    desc: str = ""
    level: str = "school"
    sort: int = 0


class NoteIn(BaseModel):
    emoji: str = Field(default="✏️", max_length=8)
    text: str = Field(min_length=1, max_length=120)
    mood: ColorKey = "teal"
    sort: int = 0


class NoteOut(ORMModel):
    id: int
    emoji: str = ""
    text: str = ""
    mood: str = "teal"
    ts: int = 0
    sort: int = 0


class FriendLinkIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    url: str = Field(min_length=1, max_length=300)
    emoji: str = Field(default="🔗", max_length=8)
    desc: str = Field(default="", max_length=120)
    sort: int = 0


class FriendLinkOut(ORMModel):
    id: int
    name: str = ""
    url: str = ""
    emoji: str = ""
    desc: str = ""
    sort: int = 0


class SongIn(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    artist: str = Field(default="", max_length=60)
    emoji: str = Field(default="🎵", max_length=8)
    song_id: str = Field(min_length=1, max_length=40)
    note: str = Field(default="", max_length=120)
    sort: int = 0


class SongOut(ORMModel):
    id: int
    title: str = ""
    artist: str = ""
    emoji: str = ""
    song_id: str = ""
    note: str = ""
    sort: int = 0


# ---------------- 相册 ----------------


class PhotoIn(BaseModel):
    file: str = Field(min_length=1, max_length=200)
    title: str = Field(default="", max_length=80)
    desc: str = Field(default="", max_length=400)
    category: str = Field(default="", max_length=30)
    shot_at: str = Field(default="", max_length=20)
    width: int = 0
    height: int = 0
    shown: int = Field(default=1, ge=0, le=1)
    sort: int = 0


class PhotoOut(ORMModel):
    id: int
    file: str = ""
    title: str = ""
    desc: str = ""
    category: str = ""
    shot_at: str = ""
    width: int = 0
    height: int = 0
    shown: int = 1
    sort: int = 0
    ts: int = 0


# ---------------- 互动 ----------------


class MessageIn(BaseModel):
    name: str = Field(default="匿名", max_length=20)
    body: str = Field(min_length=1, max_length=140)
    color: ColorKey = "pink"

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        v = v.strip()
        return v or "匿名"


class ThreadOut(ORMModel):
    id: int
    role: str = "guest"
    body: str = ""
    ts: int = 0


class MessageOut(ORMModel):
    id: int
    name: str = ""
    body: str = ""
    color: str = "pink"
    ts: int = 0
    reply: str = ""
    threads: list[ThreadOut] = []


class ThreadIn(BaseModel):
    token: str = Field(min_length=1, max_length=64)
    body: str = Field(min_length=1, max_length=140)


class QuestionIn(BaseModel):
    body: str = Field(min_length=1, max_length=200)


class QuestionOut(ORMModel):
    id: int
    body: str = ""
    ts: int = 0
    answer: str = ""
    answered_ts: int = 0


class LikeIn(BaseModel):
    page: str = Field(min_length=1, max_length=40)


class NoticeIn(BaseModel):
    body: str = Field(min_length=1, max_length=100)


class CountdownIn(BaseModel):
    title: str = Field(min_length=1, max_length=40)
    target: str = Field(min_length=1, max_length=20)
    emoji: str = Field(default="⏳", max_length=8)


# ---------------- 站点与认证 ----------------


class SiteInfo(BaseModel):
    site_owner: str = "至尊杰"
    site_name: str = "至尊杰的小窝"
    site_school: str = "燕京理工学院"
    site_major: str = "计算机科学与技术"
    site_grade: str = "2026 级"
    site_focus: str = "智能车 AI"
    site_slogan: str = "learning and building"
    site_credit: str = "纯手搓 + AI 协作"
    site_start_year: str = "2026"


class LoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)
    captcha: str = Field(default="", max_length=10)


class PasswordChangeIn(BaseModel):
    old: str = Field(min_length=1, max_length=200)
    new: str = Field(min_length=6, max_length=200)


MessageOut.model_rebuild()
