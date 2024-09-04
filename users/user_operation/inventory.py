from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from pathlib import Path
import sys

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.backend.users.database.models import User, Stock, Transaction, UserStock
from src.backend.utils.thread import MultiThreadManager

class Inventory:
    def __init__(self,Session: Session) -> None:
        self.Session = Session
        self.fee = 0.001425
        self.tax = 0.003
        
    def buy_stock(self, username: str, stock_id: str, stock_name: str, quantity: int, recent_price: float):
        with self.Session() as session:
            fee = self.fee
            final_buy_price = recent_price*(1+fee)
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return "User does not exist", None

            if user.assets < final_buy_price * quantity * 1000:
                return "資產不足夠買", None

            if quantity <= 0:
                return "給我好好買!", None

            stock = session.query(Stock).filter(Stock.id == stock_id).first()
            if not stock:
                stock = Stock(id=stock_id, name=stock_name)
                session.add(stock)

            # 增加购入交易记录
            transaction = Transaction(user_id=user.id, stock_id=stock.id, transaction_type='buy',
                                    quantity=quantity, price_per_unit=final_buy_price,
                                    timestamp=datetime.utcnow() + timedelta(hours=8))
            session.add(transaction)

            # 更新或创建用户持股记录
            user_stock = session.query(UserStock).filter_by(user_id=user.id, stock_id=stock.id).first()
            if user_stock:
                total_quantity = user_stock.quantity + quantity
                total_cost = (user_stock.price_per_unit * user_stock.quantity) + (final_buy_price * quantity)
                user_stock.price_per_unit = total_cost / total_quantity
                user_stock.quantity = total_quantity
            else:
                user_stock = UserStock(user_id=user.id, stock_id=stock.id, quantity=quantity, price_per_unit=final_buy_price)
                session.add(user_stock)

            user.assets -= final_buy_price * quantity * 1000
            session.commit()
            return "買入成功", user_stock
        
    def sell_stock(self, username: str, stock_id: str, quantity: int, recent_price: float):
        with self.Session() as session:
            fee = self.fee
            tax = self.tax
            final_sell_price = recent_price*(1-fee-tax)
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return "User does not exist", None

            user_stock = session.query(UserStock).filter_by(user_id=user.id, stock_id=stock_id).first()
            if not user_stock or user_stock.quantity < quantity:
                return "庫存股票不足", None

            transactions = session.query(Transaction).filter_by(user_id=user.id, stock_id=stock_id, transaction_type='buy').order_by(Transaction.timestamp).all()
            
            total_sold = 0
            for transaction in transactions:
                if total_sold >= quantity:
                    break
                sell_quantity = min(transaction.quantity, quantity - total_sold)
                transaction.quantity -= sell_quantity
                total_sold += sell_quantity

                profit_loss = (final_sell_price - transaction.price_per_unit) * sell_quantity
                sell_transaction = Transaction(
                    user_id=user.id, stock_id=stock_id, transaction_type='sell',
                    quantity=sell_quantity, price_per_unit=transaction.price_per_unit,
                    sold_price=final_sell_price, sold_timestamp=datetime.utcnow() + timedelta(hours=8),
                    profit_loss=profit_loss, timestamp=transaction.timestamp
                )
                session.add(sell_transaction)

                if transaction.quantity == 0:
                    session.delete(transaction)

            user_stock.quantity -= quantity
            if user_stock.quantity == 0:
                session.delete(user_stock)
            else:
                remaining_transactions = [t for t in transactions if t.quantity > 0]
                total_remaining_quantity = sum(t.quantity for t in remaining_transactions)
                total_cost = sum(t.price_per_unit * t.quantity for t in remaining_transactions)
                user_stock.price_per_unit = total_cost / total_remaining_quantity if total_remaining_quantity > 0 else 0

            user.assets += final_sell_price * quantity * 1000
            session.commit()
            return "賣出成功", user_stock
        
    def get_user_details(self, username: str,get_recent_price):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return None, "User not found"

            # 使用多线程获取股票价格
            multithread = MultiThreadManager()
            for us in user.stocks:
                multithread.add_thread(get_recent_price, (us.stock.id,))
            multithread.start_threads()
            recent_prices, exceptions = multithread.get_results_in_order()

            if exceptions:
                print("Exceptions occurred:", exceptions)

            # 检查 recent_prices 是否包含 None，并确保所有元素都是字典
            filtered_prices = [price for price in recent_prices if price and isinstance(price, dict)]

            # 构建 price_map，确保所有元素都能被正确处理
            price_map = {price['code']: price['close'] for price in filtered_prices if 'code' in price and 'close' in price}

            stocks_details = [
                {
                    'stock_id': us.stock.id,
                    'name': us.stock.name,
                    'price_per_unit': us.price_per_unit,
                    'quantity': us.quantity,
                    'recent_price': float(price_map[us.stock.id]) if us.stock.id in price_map else 0
                }
                for us in user.stocks
            ]
            
            transactions_details = [
                {
                    'transaction_id': tx.id,
                    'stock_id': tx.stock.id,
                    'transaction_type': tx.transaction_type,
                    'quantity': tx.quantity,
                    'price_per_unit': tx.price_per_unit,
                    'timestamp': tx.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'sold_price': getattr(tx, 'sold_price', None),
                    'sold_timestamp': getattr(tx, 'sold_timestamp', None).strftime('%Y-%m-%d %H:%M:%S') if getattr(tx, 'sold_timestamp', None) else None,
                    'profit_loss': getattr(tx, 'profit_loss', None)
                }
                for tx in user.transactions if tx.transaction_type == 'sell'
            ]
            return {
                'assets': user.assets,
                'stocks': stocks_details,
                'transactions': transactions_details
            }, None
