import datetime
from database import BaseModel, engine
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship


class Genre(BaseModel):
    __tablename__ = "genre"

    genre_id = Column(Integer, primary_key=True)
    name_genre = Column(String(100), nullable=False)

    def __str__(self):
        return f"Жанр: {self.name_genre}"


class Author(BaseModel):
    __tablename__ = "author"

    author_id = Column(Integer, primary_key=True)
    name_author = Column(String(100), nullable=False)

    def __str__(self):
        return f"Автор: {self.name_author}"


class City(BaseModel):
    __tablename__ = "city"

    city_id = Column(Integer, primary_key=True)
    name_city = Column(String(100), nullable=False)
    days_delivery = Column(Integer, nullable=False)

    def __str__(self):
        return f"Город: {self.name_city}, Доставка: {self.days_delivery} дн."


class Book(BaseModel):
    __tablename__ = "book"

    book_id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author_id = Column(Integer, ForeignKey("author.author_id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genre.genre_id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    amount = Column(Integer, nullable=False, default=0)

    author = relationship("Author", back_populates="books")
    genre = relationship("Genre", back_populates="books")

    def __str__(self):
        return f"Книга: {self.title}, Цена: {self.price} руб."


class Client(BaseModel):
    __tablename__ = "client"

    client_id = Column(Integer, primary_key=True)
    name_client = Column(String(100), nullable=True)
    city_id = Column(Integer, ForeignKey("city.city_id"), nullable=False)
    email = Column(String(254), nullable=True)

    city = relationship("City", back_populates="clients")
    buys = relationship("Buy", back_populates="client", cascade="all, delete-orphan")

    def __str__(self):
        return f"Клиент: {self.name_client}, Email: {self.email}"


class Buy(BaseModel):
    __tablename__ = "buy"

    buy_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.client_id"), nullable=False)

    client = relationship("Client", back_populates="buys")
    buy_books = relationship("BuyBook", back_populates="buy", cascade="all, delete-orphan")
    buy_steps = relationship("BuyStep", back_populates="buy", cascade="all, delete-orphan")

    def __str__(self):
        return f"Покупка #{self.buy_id} клиента {self.client.name_client}"


class Step(BaseModel):
    __tablename__ = "step"

    step_id = Column(Integer, primary_key=True)
    name_step = Column(String(100), nullable=False)

    def __str__(self):
        return f"Этап: {self.name_step}"


class BuyBook(BaseModel):
    __tablename__ = "buy_book"

    buy_book_id = Column(Integer, primary_key=True)
    buy_id = Column(Integer, ForeignKey("buy.buy_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    amount = Column(Integer, nullable=False)

    buy = relationship("Buy", back_populates="buy_books")
    book = relationship("Book", back_populates="buy_books")

    def __str__(self):
        return f"Покупка книги #{self.book_id} в заказе #{self.buy_id}, {self.amount} шт."


class BuyStep(BaseModel):
    __tablename__ = "buy_step"

    buy_step_id = Column(Integer, primary_key=True)
    buy_id = Column(Integer, ForeignKey("buy.buy_id"), nullable=False)
    step_id = Column(Integer, ForeignKey("step.step_id"), nullable=False)
    date_step_beg = Column(DateTime, default=datetime.datetime.utcnow)
    date_step_end = Column(DateTime, nullable=True)

    buy = relationship("Buy", back_populates="buy_steps")
    step = relationship("Step", back_populates="buy_steps")

    def __str__(self):
        return f"Этап '{self.step.name_step}' для покупки #{self.buy_id}"


#BaseModel.metadata.create_all(engine)
