from sqlalchemy.orm import Session

from pathlib import Path
import sys

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
    
from src.backend.users.database.models import User, FavoriteStock,Stock

class Favor:
    def __init__(self,Session: Session) -> None:
        self.Session = Session
    
    def add_favorite_stock(self, username:str, stock_id:str,stock_name:str):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).scalar()
            stock = session.query(Stock).filter(Stock.id == stock_id).scalar()
            if not stock:
                new_stock = Stock(id=stock_id, name=stock_name)
                session.add(new_stock)
                session.commit()               
            existing_favorite = session.query(FavoriteStock).filter_by(user_id=user.id, stock_id=stock_id).scalar()
            if existing_favorite:
                return '已加入自選',False
            new_favorite = FavoriteStock(user_id=user.id, stock_id=stock_id)
            session.add(new_favorite)
            session.commit()
            return '加入成功',True
        
    def remove_favorite_stock(self, username:str, stock_id:str):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).scalar()
            if user:
                favorite_stock = session.query(FavoriteStock).filter(FavoriteStock.user_id == user.id, FavoriteStock.stock_id == stock_id).scalar()
                if favorite_stock:
                    session.delete(favorite_stock)
                    session.commit()
                    return "Stock removed from favorites", True
            return "User or favorite stock not found", False
        
    def get_fav_stock_ids(self, username:str):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return []
            favorite_stocks = session.query(FavoriteStock).filter(FavoriteStock.user_id == user.id).all()
            # print(favorite_stocks)
            if not favorite_stocks:
                return []
            favorite_stock_ids = [fav.stock_id for fav in favorite_stocks]
            return favorite_stock_ids