from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import os

password= os.environ.get('DATABASE_PASSWORD')

DATABASE_URL=f"postgresql+asyncpg://postgres:{password}@localhost:5432/cashcow_dev_2478"

engine= create_async_engine(DATABASE_URL, echo= True)

AsyncSessionLocal= async_sessionmaker(engine, expire_on_commit= False)
