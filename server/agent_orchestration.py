import os
import certifi
from typing import TypedDict,Annotated
import operator
import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from graph import graph

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    prepare_threshold=0,
    row_factory=dict_row,
)
checkpoint_saver = PostgresSaver(_conn)
checkpoint_saver.setup()

travel_graph =graph.compile(checkpointer=checkpoint_saver)