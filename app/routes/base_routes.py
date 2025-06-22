from typing import Type, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.dependencies import require_admin
from app.crud.base_crud import BaseCRUD, paginate


class BaseCRUDRouter:
    """Generic CRUD router to eliminate repetitive route patterns"""

    def __init__(self,
                 model: Type,
                 create_schema: Type[BaseModel],
                 response_schema: Type[BaseModel],
                 prefix: str,
                 tags: List[str]):
        self.model = model
        self.crud = BaseCRUD(model)
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.router = APIRouter(prefix=prefix, tags=tags)
        self._setup_routes()

    def _setup_routes(self):
        """Setup standard CRUD routes"""

        @self.router.post("/", response_model=self.response_schema)
        def create_item(item: self.create_schema, db: Session = Depends(get_db), admin=Depends(require_admin)):
            return self.crud.create(db, obj_in=item)

        @self.router.get("/{item_id}", response_model=self.response_schema)
        def get_item(item_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
            item = self.crud.get(db, id=item_id)
            if not item:
                raise HTTPException(404, f"{self.model.__name__} not found")
            return item

        @self.router.get("/", response_model=List[self.response_schema])
        def list_items(
                page: int = Query(1, ge=1),
                size: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db),
                admin=Depends(require_admin)
        ):
            query = db.query(self.model)
            return paginate(query, page, size)

        @self.router.delete("/{item_id}")
        def delete_item(item_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
            item = self.crud.remove(db, id=item_id)
            if not item:
                raise HTTPException(404, f"{self.model.__name__} not found")
            return {"deleted": True}


def create_crud_router(model, create_schema, response_schema, prefix, tags):
    """Factory function to create CRUD routers"""
    return BaseCRUDRouter(model, create_schema, response_schema, prefix, tags).router