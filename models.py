from datetime import datetime
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Float, Date


class SpimexTradingResults(Base):
    __tablename__ = "spimex_trading_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange_product_id = Column(String, nullable=False)
    exchange_product_name = Column(String, nullable=False)
    oil_id = Column(String, nullable=False)
    delivery_basis_id = Column(String, nullable=False)
    delivery_basis_name = Column(String, nullable=False)
    delivery_type_id = Column(String, nullable=False)
    volume = Column(Integer, nullable=True)
    total = Column(Float, nullable=True)
    count = Column(Integer, nullable=True)
    date = Column(Date, nullable=False)
    created_on = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
