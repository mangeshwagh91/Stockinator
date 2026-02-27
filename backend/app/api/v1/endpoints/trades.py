"""Trade management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date
from typing import Optional

from app.api.dependencies import get_database
from app.models.trade import Trade, TradeStatus, TradeType
from app.schemas.trade import (
    TradeCreate, TradeResponse, TradeUpdate,
    TradeListResponse, TradeSummary
)
from app.services.broker_service import broker_service

router = APIRouter()


@router.post("/", response_model=TradeResponse)
async def create_trade(
    trade: TradeCreate,
    db: Session = Depends(get_database)
):
    """Create and execute a new trade"""
    try:
        # Place order with broker
        order_result = broker_service.place_order(
            symbol=trade.symbol,
            side=trade.trade_type.value,
            quantity=trade.quantity,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit
        )
        
        # Create trade record
        db_trade = Trade(
            symbol=trade.symbol,
            trade_type=trade.trade_type,
            quantity=trade.quantity,
            entry_price=order_result.get('filled_price'),
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            success_score=trade.success_score,
            broker_order_id=order_result.get('broker_order_id'),
            status=TradeStatus.PENDING,
            notes=trade.notes,
            is_paper=trade.is_paper
        )
        
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)
        
        return db_trade
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TradeListResponse)
async def list_trades(
    db: Session = Depends(get_database),
    symbol: Optional[str] = None,
    status: Optional[TradeStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """List trades with filtering"""
    query = db.query(Trade)
    
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if status:
        query = query.filter(Trade.status == status)
    
    query = query.order_by(desc(Trade.created_at))
    
    total = query.count()
    trades = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return TradeListResponse(
        trades=trades,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    db: Session = Depends(get_database)
):
    """Get a specific trade by ID"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.patch("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: int,
    trade_update: TradeUpdate,
    db: Session = Depends(get_database)
):
    """Update a trade"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    update_data = trade_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trade, field, value)
    
    # Calculate P&L if closing
    if trade_update.exit_price and trade.entry_price:
        if trade.trade_type == TradeType.BUY:
            pnl = (trade_update.exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - trade_update.exit_price) * trade.quantity
        
        trade.profit_loss = pnl - trade.brokerage - trade.slippage
        trade.profit_loss_percentage = (pnl / (trade.entry_price * trade.quantity)) * 100
    
    db.commit()
    db.refresh(trade)
    return trade


@router.delete("/{trade_id}")
async def cancel_trade(
    trade_id: int,
    db: Session = Depends(get_database)
):
    """Cancel a pending trade"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status not in [TradeStatus.PENDING, TradeStatus.PARTIAL]:
        raise HTTPException(status_code=400, detail="Cannot cancel filled trade")
    
    # Cancel with broker
    try:
        if trade.broker_order_id:
            broker_service.cancel_order(trade.broker_order_id)
        
        trade.status = TradeStatus.CANCELLED
        db.commit()
        
        return {"message": "Trade cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary/stats", response_model=TradeSummary)
async def get_trade_summary(
    db: Session = Depends(get_database),
    days: int = Query(30, ge=1, le=365)
):
    """Get summary statistics for trades"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    trades = db.query(Trade).filter(
        Trade.created_at >= cutoff_date,
        Trade.status == TradeStatus.FILLED,
        Trade.profit_loss.isnot(None)
    ).all()
    
    if not trades:
        return TradeSummary(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_profit_loss=0,
            win_rate=0,
            avg_profit=0,
            avg_loss=0,
            best_trade=0,
            worst_trade=0
        )
    
    winning_trades = [t for t in trades if t.profit_loss > 0]
    losing_trades = [t for t in trades if t.profit_loss <= 0]
    
    return TradeSummary(
        total_trades=len(trades),
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        total_profit_loss=sum(t.profit_loss for t in trades),
        win_rate=(len(winning_trades) / len(trades)) * 100,
        avg_profit=sum(t.profit_loss for t in winning_trades) / len(winning_trades) if winning_trades else 0,
        avg_loss=sum(t.profit_loss for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        best_trade=max((t.profit_loss for t in trades), default=0),
        worst_trade=min((t.profit_loss for t in trades), default=0)
    )


@router.get("/positions/open")
async def get_open_positions(asset_type: str = "stock"):
    """Get currently open positions from broker"""
    try:
        positions = broker_service.get_positions(asset_type)
        return {
            "positions": positions,
            "count": len(positions),
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/account/info")
async def get_account_info(asset_type: str = "stock"):
    """Get account information from broker"""
    try:
        account = broker_service.get_account(asset_type)
        return {
            "account": account,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
