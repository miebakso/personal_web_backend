from operator import and_
from fastapi import APIRouter, Depends, HTTPException, Body
from app.dependencies import get_db_connection
from app.models.transaction import TransactionCreate, TransactionUpdate, TransationGetRequest
from app.schema import Category, Transaction
from typing import Union, List
from datetime import datetime
from sqlalchemy import and_

router = APIRouter(
    prefix="/transations",
    tags=["transations"],
)

# Return all the categories order by their ID
@router.get("/")
async def get_transations(
        t_request: TransationGetRequest,
        session= Depends(get_db_connection)
    ):
    query = session.query(Transaction).join(Category)
    
    # Filter categories if specified
    if t_request.categor_id:
        query = query.filter(Transaction.category_id.in_(tuple(t_request.category_ids)))
    
    # transations order
    order = Transaction.date.asc()
    if not t_request.date_asc :
        order = Transaction.date.desc()
    query = query.order_by(order)

    # filter start date, end date or both
    if t_request.start_date is not None and t_request.end_date is not None:
        query = query.filter(and_(Transaction.date >= t_request.start_date, Transaction.date <= t_request.end_date))
    else: 
        if t_request.start_date is not None:
            query = query.filter(Transaction.date >= t_request.start_date)
        if t_request.end_date is not None:
            query = query.filter(Transaction.date <= t_request.end_date)
    
    # filter offset if specified
    if t_request.page is not None:
        query = query.offset(t_request.page*t_request.page_size - t_request.page_size)
    
    # filter page size if not specified
    if t_request.page_size is not None:
        query = query.limit(t_request.page_size)
    return query.all()

# Return a specific trasantion by their ID
@router.get("/{trascation_id}")
async def get_transation(trascation_id: int, session = Depends(get_db_connection)):
    return session.query(Transaction).filter(Transaction.id == trascation_id).join(Category).first()
    
@router.post("/")
async def add_transation(transaction: TransactionCreate, session = Depends(get_db_connection)):
    db_transactions = Transaction()
    transation_data = transaction.dict()
    for key, value in transation_data.items():
        setattr(db_transactions, key, value)
    # Handle duplicate values
    session.add(db_transactions)
    session.commit()
    session.refresh(db_transactions)
    return db_transactions

# Update a category by their ID
@router.put("/{transation_id}")
async def update_transation(transation_id:int, transaction: TransactionUpdate, session = Depends(get_db_connection)):
    db_transactions = session.query(Transaction).filter(Transaction.id == transation_id).first()
    if not db_transactions:
        raise HTTPException(status_code=404, detail="Transaction Not Found")
    transation_data = transaction.dict()
    for key, value in transation_data.items():
        setattr(db_transactions, key, value)
    session.add(db_transactions)
    session.commit()
    session.refresh(db_transactions)
    return db_transactions

# Removed a category by their ID
@router.delete("/{transation_id}")
async def remove_category(transation_id:int, session = Depends(get_db_connection)):
    db_transaction = session.query(Transaction).filter(Transaction.id == transation_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transation you're trying to removed not found")
    session.delete(db_transaction)
    session.commit()
    return {'msg':'Transation has been deleted'}
