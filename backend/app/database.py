import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

load_dotenv()

password= os.environ.get('DATABASE_PASSWORD')
host= os.environ.get("DATABASE_HOST", "localhost")
database= os.environ.get("DATABASE_NAME", "cashcow_dev_2478")
username= os.environ.get("DATABASE_USERNAME", "postgres")
port= os.environ.get("DATABASE_PORT", "5432")

DATABASE_URL = (
    f"postgresql+asyncpg://{username}:{password}"
    f"@{host}:{port}/{database}"
)

engine_options= {
    "echo": False,
    "connect_args": {
        "timeout": 2,
        "command_timeout": 5,
    },
}
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    engine_options["poolclass"] = NullPool
else:
    engine_options["pool_timeout"]= 2

engine= create_async_engine(DATABASE_URL, **engine_options)
AsyncSessionLocal= async_sessionmaker(engine, expire_on_commit= False)
