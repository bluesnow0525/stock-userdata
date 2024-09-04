from sqlalchemy.orm import Session

from pathlib import Path
import sys

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
    
from src.backend.users.database.models import ActivationCode,User
import uuid

class Activationcode:
    def __init__(self,Session: Session) -> None:
        self.Session = Session
        
    def generate_activation_codes(self, num_codes=20):
        codes = {str(uuid.uuid4()) for _ in range(num_codes)}
        vip_codes = {str(uuid.uuid4()) for _ in range(num_codes)}
        return list(codes), list(vip_codes)
    
    def initialize_activation_codes(self):
        with self.Session() as session:
            existing_codes_count = session.query(ActivationCode).count()
    
            if existing_codes_count >= 20:
                print("已有足夠的認證碼，不需要創建新的認證碼")
                return []

            num_codes_to_create = 20 - existing_codes_count
            codes, vip_codes = self.generate_activation_codes(num_codes_to_create)
            
            for code, vip_code in zip(codes, vip_codes):
                activation_code = ActivationCode(code=code, vip_code=vip_code)
                session.add(activation_code)
            
            session.commit()
            return codes, vip_codes
        
    def get_available_activation_codes(self):
        with self.Session() as session:
            available_codes = session.query(ActivationCode).filter_by(used=False).all()
            return [(code.code) for code in available_codes]
    
    def add_activation_codes(self, num_codes):
        with self.Session() as session:
            codes, vip_codes = self.generate_activation_codes(num_codes)
            for code, vip_code in zip(codes, vip_codes):
                activation_code = ActivationCode(code=code, vip_code=vip_code)
                session.add(activation_code)
            session.commit()
            return codes, vip_codes
        
    def check_vip_code(self, username, vip_code):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                activation_code = session.query(ActivationCode).filter(
                    ActivationCode.id == user.activation_code_id,
                    ActivationCode.vip_code == vip_code,
                ).first()
                if activation_code:
                    user.vip = True
                    session.commit()
                    return True, "VIP code is valid. User has been updated to VIP."
            return False, "Invalid VIP code or user not found."
        
    def cancel_vip(self, username):
        with self.Session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user and user.vip:
                activation_code = session.query(ActivationCode).filter(
                    ActivationCode.id == user.activation_code_id,
                    ActivationCode.used == True
                ).first()
                if activation_code:
                    user.vip = False
                    new_vip_code = str(uuid.uuid4())
                    activation_code.vip_code = new_vip_code
                    session.commit()
                    return True
            return False