from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from .user_database import Base
from datetime import datetime

from pathlib import Path
import sys
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
from src.backend import config
from src.backend.utils.sqlalchemy_tool import get_engine

class ActivationCode(Base):
    __tablename__ = 'activation_codes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(255), unique=True, nullable=False)
    vip_code = Column(String(255), unique=True, nullable=False)
    used = Column(Boolean, default=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(Text,nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    vip = Column(Boolean, default=False)
    root = Column(Boolean, default=False)
    line_id = Column(Text, default='')
    activation_code_id = Column(Integer, ForeignKey('activation_codes.id'), nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    assets = Column(Float, default=0.0)
    stocks = relationship('UserStock', back_populates='user', cascade="all, delete-orphan")
    transactions = relationship('Transaction', back_populates='user', cascade="all, delete-orphan")
    favorite_stocks = relationship('FavoriteStock', back_populates='user', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    user_stocks = relationship('UserStock', back_populates='stock', cascade="all, delete-orphan")
    transactions = relationship('Transaction', back_populates='stock', cascade="all, delete-orphan")
    favorites = relationship('FavoriteStock', back_populates='stock', cascade="all, delete-orphan")
    
class UserStock(Base):
    __tablename__ = 'user_stocks'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    stock_id = Column(String(20), ForeignKey('stocks.id'), primary_key=True)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    stock = relationship('Stock', back_populates='user_stocks')
    user = relationship('User', back_populates='stocks')

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    stock_id = Column(String(20), ForeignKey('stocks.id'))
    transaction_type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sold_price = Column(Float, nullable=True)
    sold_timestamp = Column(DateTime, nullable=True)
    profit_loss = Column(Float, nullable=True)
    user = relationship('User', back_populates='transactions')
    stock = relationship('Stock', back_populates='transactions')

class FavoriteStock(Base):
    __tablename__ = 'favorite_stocks'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    stock_id = Column(String(20), ForeignKey('stocks.id'), primary_key=True)
    user = relationship('User', back_populates='favorite_stocks')
    stock = relationship('Stock', back_populates='favorites')
    
Base.metadata.create_all(get_engine(config.USER_DATABASE))