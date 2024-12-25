from typing import List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import TodoItem as TodoItemModel

Base.metadata.create_all(bind=engine)

app = FastAPI()


class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False


class TodoCreateList(BaseModel):
    items_list: List[TodoCreate]


class TodoItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False

    class Config:
        orm_mode = True


class TodoItemList(BaseModel):
    items: List[TodoItem]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Добавлена функция поиска по title
@app.get("/items", response_model=List[TodoItem])
def get_items(db: Session = Depends(get_db), title: Union[str, None] = None):
    items = db.query(TodoItemModel).all() if title is None else db.query(TodoItemModel).filter(
        TodoItemModel.title == title)
    return items


@app.get("/items/{item_id}", response_model=TodoItem)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TodoItemModel).filter(TodoItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/items", response_model=TodoItem)
def create_item(item: TodoCreate, db: Session = Depends(get_db)):
    new_item = TodoItemModel(
        title=item.title,
        description=item.description,
        completed=item.completed
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


# Добавлена возможность постинга списка
@app.post("/items/list", response_model=TodoItemList)
def create_item_by_list(lst: TodoCreateList, db: Session = Depends(get_db)):
    items = [TodoItemModel(title=item.title,
                           description=item.description,
                           completed=item.completed) for item in lst.items_list]
    db.add_all(items)
    db.commit()
    new = []
    for i in items:
        new.append({"id": i.id, "title": i.title,
                    "description": i.description, "completed": i.completed})
    new_lst = TodoItemList(items=new)

    return new_lst


@app.put("/items/{item_id}", response_model=TodoItem)
def update_item(item_id: int, item: TodoCreate, db: Session = Depends(get_db)):
    db_item = db.query(TodoItemModel).filter(TodoItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.title = item.title
    db_item.description = item.description
    db_item.completed = item.completed
    db.commit()
    db.refresh(db_item)
    return db_item


# Удаление ВСЕГО всписка
@app.delete("/items/all")
def delete_all(db: Session = Depends(get_db)):
    db.query(TodoItemModel).delete()
    db.commit()
    return {"message": "All item deleted"}


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(TodoItemModel).filter(TodoItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}
