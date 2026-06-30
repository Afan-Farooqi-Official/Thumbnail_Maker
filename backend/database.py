from sqlmodel import SQLModel, create_engine, Session
from config import DATABASE_URL

# Create the database engine, which will be used to connect to the database. The `check_same_thread` argument is set to False to allow the use of the engine in a multi-threaded environment, which is common in web applications.
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Create the database tables based on the models defined in the application. This function should be called at the start of the application to ensure that the necessary tables are created in the database.
def create_tables():
    SQLModel.metadata.create_all(engine)

# Provide a session generator function that can be used to create a new database session. This function uses a context manager to ensure that the session is properly closed after use, which helps prevent resource leaks and ensures that database connections are managed efficiently.
def get_session():
    with Session(engine) as session:
        yield session