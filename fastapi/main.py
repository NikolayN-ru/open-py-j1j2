from typing import Optional
from fastapi import FastAPI, Request
import httpx
from sqlalchemy import create_engine, Column, Integer, String, DateTime, desc, exc
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

app = FastAPI()

engine = create_engine("postgresql://postgres:password@db/mydatabase")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base(bind=engine)
db = SessionLocal()

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    question_text = Column(String)
    answer_text = Column(String)
    created_date = Column(DateTime)

try:
    Base.metadata.create_all()
    print("Таблица 'questions' создана")
except exc.SQLAlchemyError as e:
    print("Произошла ошибка при создании таблицы 'questions':", str(e))

def get_previous_question() -> Optional[Question]:
    session = SessionLocal()
    previous_question = session.query(Question).order_by(desc(Question.created_date)).first()
    session.close()
    return previous_question

@app.get("/previous-question")
async def previous_question():
    previous_question = get_previous_question()
    if previous_question:
        return previous_question
    else:
        return {}
    
@app.post("/questions")
async def create_questions(questions_num: int):
    unique_questions = []

    while len(unique_questions) < questions_num:
        api_url = "https://jservice.io/api/random"
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)

        if response.status_code == 200:
            question = response.json()[0]
            db = SessionLocal()
            existing_question = db.query(Question).filter_by(question_text=question["question"]).first()
            if existing_question is None and question not in unique_questions:
                new_question = Question(
                    question_text=question["question"],
                    answer_text=question["answer"],
                    created_date=datetime.datetime.now()
                )
                db.add(new_question)
                unique_questions.append(question)
            db.commit()
            db.close()

    return {"message": "Уникальные вопросы сохранены в базе данных"}