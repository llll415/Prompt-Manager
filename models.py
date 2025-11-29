from flask_login import UserMixin
from datetime import datetime
from extensions import db
from flask import request

# 多对多关联表：图片与标签
image_tags = db.Table('image_tags',
                      db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
                      db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                      )


class User(UserMixin, db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))


class Image(db.Model):
    """核心作品模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(50), default='匿名')
    file_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    prompt = db.Column(db.Text)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))  # txt2img / img2img
    status = db.Column(db.String(20), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 统计数据
    views_count = db.Column(db.Integer, default=0)
    copies_count = db.Column(db.Integer, default=0)
    heat_score = db.Column(db.Integer, default=0, index=True)

    # 关联
    tags = db.relationship('Tag', secondary=image_tags, backref='images')
    refs = db.relationship('ReferenceImage', backref='image', cascade="all, delete-orphan",
                           order_by="ReferenceImage.position")

    def to_dict(self):
        """序列化为字典，用于 API 或导出"""

        def _get_full_url(path):
            """辅助函数：确保返回的是带域名的完整 URL"""
            if not path:
                return None
            if path.startswith(('http://', 'https://')):
                return path
            # 本地路径，拼接当前请求的域名
            return request.url_root.rstrip('/') + path

        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "prompt": self.prompt,
            "description": self.description,
            "type": self.type,

            # 主图和缩略图都处理成绝对路径
            "file_path": _get_full_url(self.file_path),
            "thumbnail_path": _get_full_url(self.thumbnail_path),

            "tags": [t.name for t in self.tags],

            # 参考图列表也处理成绝对路径
            "refs": [_get_full_url(r.file_path) for r in self.refs],

            "heat_score": self.heat_score,
            "created_at": self.created_at.isoformat()
        }


class ReferenceImage(db.Model):
    """参考图模型"""
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, default=0)


class Tag(db.Model):
    """标签模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_sensitive = db.Column(db.Boolean, default=False)