from .database.user_database import Session, Base, engine
from .user_operation.favor import Favor
from .user_operation.user_info import UserInfo
from .user_operation.inventory import Inventory
from .user_operation.activationcode import Activationcode

from pathlib import Path
import sys
src_path = Path(__file__).resolve().parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
from src.backend.utils.memory_management import Redis

class UserManager:
    def __init__(self,cache:Redis=None):
        if cache is None:
            self.cache = Redis()
            self.parse_cache = False
        else:
            self.cache = cache
            self.parse_cache = True

        # Base.metadata.create_all(bind=engine)
        self.Session = Session
        self.favor = Favor(Session)
        self.userinfo = UserInfo(Session)
        self.inventory = Inventory(Session)
        self.activationcode = Activationcode(Session)

        self.cache.set('user_manager',self,permanent=True)
        
    def close(self):
        self.cache.delete('user_manager')
        if not self.parse_cache:
            self.cache.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close


if __name__ == "__main__":
    user_manager = UserManager()
    user_manager.initialize_activation_codes()
    # user_manager.add_activation_codes(1)
    user_manager.get_available_activation_codes()
    # user_manager.get_vip_code('username')
    # user_manager.cancel_vip('username')