from app.database import Base, engine
import app.models

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)