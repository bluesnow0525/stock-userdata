from pathlib import Path
import sys

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sqlalchemy.orm import Session
from src.backend.users.database.models import User,ActivationCode
from src.backend.users.mail.mail import send_email
from datetime import datetime, timedelta

class UserInfo:
    def __init__(self,Session: Session) -> None:
        self.Session = Session
        
    def isuser(self, username):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return True
            else:
                return False
    
    def login_user(self, username: str, password: str):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False,False,False
            if user and user.check_password(password) and user.is_active:
                return True,True,user.vip
            if not user.is_active:
                if user and user.check_password(password):
                    return True,False,False
            return False,False,False
        
    def register_user(self, username: str, password: str, email:str, activation_code_str:str):
        with self.Session() as session:
            if session.query(User).filter(User.username == username).first() or session.query(User).filter(User.email == email).first():
                return None,True  # User already exists
            activation_code = session.query(ActivationCode).filter_by(code=activation_code_str, used=False).first()
            if activation_code:
                expiry_date = datetime.now() + timedelta(days=30)
                user = User(username=username, assets=10000000, email=email, activation_code_id=activation_code.id, expiry_date=expiry_date, is_active=True)
                user.set_password(password)
                activation_code.used = True
                session.add(user)            

                subject = "Registration Successful"
                body = f"Dear {username},\n\nYour registration was successful.\n\nYour credentials:\nUsername: {username}\nPassword: {password}\n\nBest regards,\nYour Team"
                try:
                    send_email(email, subject, body)
                except Exception as e:
                    # print(e)
                    return None,False
                
                session.commit()
                return user,True
            else:
                return None,False
        
    def get_user_assets(self, username: str):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return user.assets
            else:
                return None

    def update_user_status(self):
        with self.Session() as session:
            users = session.query(User).all()
            for user in users:
                if user.expiry_date < datetime.now():
                    user.is_active = False
            session.commit()
            
    def forgot_password(self, username):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                subject = "Password Reset"
                body = f"Dear {user.username},\n\nYour password is: {user.password}\n\nBest regards,\nYour Team"
                send_email(user.email, subject, body)
                return True, "Password has been sent to your email"
            return False, "user not found"
        
    def get_vip_code(self, username):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                activation_code = session.query(ActivationCode).filter(
                    ActivationCode.id == user.activation_code_id
                ).first()
                if activation_code:
                    return activation_code.vip_code
            return "User not found or VIP code not available."
        
    def check_line_id(self, line_id):
        with self.Session() as session:
            user = session.query(User).filter(User.line_id == line_id).first()
            if user:
                return user.username
            else:
                return None
            
    def check_isvip(self, username):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                if user.vip == True:
                    return user.username
                else:
                    return None
            else:
                return None
            
    def add_line_id(self, username, password, line_id):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user and user.check_password(password) and user.is_active and user.line_id == '':
                user.line_id = line_id
                session.commit()
                return True
            else:
                return False
                
    def get_all_users(self):
        with self.Session() as session:
            results = session.query(
                User.id,
                User.username,
                User.email,
                User.vip,
                ActivationCode.vip_code,
                User.expiry_date,
                User.is_active
            ).join(ActivationCode, User.activation_code_id == ActivationCode.id).all()
            
            users_info = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "vip": user.vip,
                    "vip_code": user.vip_code,
                    "expire_date": user.expiry_date.strftime('%Y-%m-%d %H:%M:%S'),
                    "isactive": user.is_active
                }
                for user in results
            ]
            return users_info

    def change_isactive(self, username, isactive):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                if isactive:
                    if user.expiry_date <= datetime.now():
                        user.expiry_date = datetime.now() + timedelta(days=30)
                    user.is_active = True
                else:
                    user.is_active = False
            session.commit()
            return True