from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, Relationship
from typing import List, Optional

import strawberry
from strawberry.fastapi import GraphQLRouter

# URL database untuk SQLite
DATABASE_URL = "sqlite:///./test.db"

# Membuat engine SQLite
engine = create_engine(DATABASE_URL, echo=True)

# Mendefinisikan model tabel Post
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    category: str
    summary: str
    author_id: int = Field(foreign_key="user.id")

    # Relasi ke model User
    author: "User" = Relationship(back_populates="posts")

# Mendefinisikan model tabel User
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

    # Relasi ke model Post
    posts: List[Post] = Relationship(back_populates="author")

# Membuat semua tabel di database
SQLModel.metadata.create_all(engine)

# Mendefinisikan tipe GraphQL untuk Post
@strawberry.type
class PostType:
    id: int
    title: str
    category: str
    summary: str
    author_id: int

# Mendefinisikan tipe GraphQL untuk User
@strawberry.type
class UserType:
    id: int
    name: str
    email: str
    posts: List[PostType]

# Resolver untuk query
@strawberry.type
class Query:

    # Mengambil user berdasarkan ID
    @strawberry.field
    def get_user(self, id: int) -> UserType:
        with Session(engine) as session:
            user = session.get(User, id)
            if not user:
                raise HTTPException(status_code=404, detail="User tidak ditemukan")
            return UserType(
                id=user.id,
                name=user.name,
                email=user.email,
                posts=[
                    PostType(
                        id=post.id,
                        title=post.title,
                        category=post.category,
                        summary=post.summary,
                        author_id=post.author_id
                    )
                    for post in user.posts
                ]
            )

    # Mengambil post berdasarkan ID
    @strawberry.field
    def get_post(self, id: int) -> PostType:
        with Session(engine) as session:
            post = session.get(Post, id)
            if not post:
                raise HTTPException(status_code=404, detail="Post tidak ditemukan")
            return PostType(
                id=post.id,
                title=post.title,
                category=post.category,
                summary=post.summary,
                author_id=post.author_id
            )

# Resolver untuk mutation
@strawberry.type
class Mutation:

    # Membuat user baru
    @strawberry.mutation
    def create_user(self, name: str, email: str) -> UserType:
        with Session(engine) as session:
            new_user = User(name=name, email=email)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return UserType(
                id=new_user.id,
                name=new_user.name,
                email=new_user.email,
                posts=[]
            )

    # Membuat post baru
    @strawberry.mutation
    def create_post(self, title: str, category: str, summary: str, author_id: int) -> PostType:
        with Session(engine) as session:
            new_post = Post(title=title, category=category, summary=summary, author_id=author_id)
            session.add(new_post)
            session.commit()
            session.refresh(new_post)
            return PostType(
                id=new_post.id,
                title=new_post.title,
                category=new_post.category,
                summary=new_post.summary,
                author_id=new_post.author_id
            )

# Menyiapkan schema dan aplikasi FastAPI
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()

# Menambahkan rute GraphQL ke aplikasi dengan prefix /graphql
app.include_router(graphql_app, prefix="/graphql")
