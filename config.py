from dataclasses import dataclass
from environs import Env

@dataclass
class Config:
    bot_token: str
    admin_id: int

def load_config() -> Config:
    env = Env()
    env.read_env()
    
    return Config(
        bot_token=env.str("BOT_TOKEN"),
        admin_id=env.int("ADMIN_ID")
    )

PRIZES = {
    "discount_10": {"name": "Сертификат на скидку 10%", "quantity": 20},
    "mug": {"name": "Кружка", "quantity": 5},
    "notebook": {"name": "Блокнот", "quantity": 5},
    "pen": {"name": "Ручка", "quantity": 5},
    "shopper": {"name": "Шоппер", "quantity": 5}
} 