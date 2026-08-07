# app/models/role.py (ОБНОВЛЁННАЯ ВЕРСИЯ)
from sqlalchemy import Column, SmallInteger, String, Table, ForeignKey, BigInteger, Index
from sqlalchemy.orm import relationship
from app.database import Base

# Ассоциативная таблица для связи many-to-many между User и Role
users_roles = Table(
    "users_roles",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", SmallInteger, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    role_title = Column(String(50), nullable=False, unique=True)
    
    # НОВЫЕ ПОЛЯ (в соответствии с изменениями БД)
    role_title_ru = Column(String(100), nullable=True, unique=True)
    role_code = Column(String(6), nullable=True, unique=True)
    
    # Связи
    users = relationship("User", secondary=users_roles, back_populates="roles")
    
    # Индексы
    __table_args__ = (
        Index("idx_roles_code", "role_code", postgresql_where=(role_code.isnot(None))),
        Index("idx_roles_title_ru", "role_title_ru"),
    )
    
    # ========== Свойства ==========
    
    @property
    def has_code(self) -> bool:
        """Есть ли у роли буквенный код"""
        return self.role_code is not None
    
    @property
    def display_title(self) -> str:
        """Отображаемое название (русское если есть, иначе английское)"""
        return self.role_title_ru or self.role_title
    
    # ========== Методы ==========
    
    def get_localized_title(self, lang: str = "ru") -> str:
        """Локализованное название роли"""
        if lang == "ru" and self.role_title_ru:
            return self.role_title_ru
        return self.role_title
    
    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_title='{self.role_title}', role_code='{self.role_code}')>"
