from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.notification import Notification
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])

@router.get("/", response_model=List[NotificationOut])
def get_my_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification)
    if current_user.role == UserRole.ADMIN:
        # Admin sees both their user notifications and general admin deal alerts
        query = query.filter(or_(Notification.user_id == current_user.id, Notification.is_for_admin == True))
    else:
        query = query.filter(Notification.user_id == current_user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    return query.order_by(Notification.created_at.desc()).limit(50).all()

@router.put("/{notif_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    if not notif.is_for_admin and notif.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    notif.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}

@router.put("/read-all", status_code=status.HTTP_200_OK)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.ADMIN:
        db.query(Notification).filter(
            or_(Notification.user_id == current_user.id, Notification.is_for_admin == True)
        ).update({"is_read": True}, synchronize_session=False)
    else:
        db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).update({"is_read": True}, synchronize_session=False)

    db.commit()
    return {"message": "All notifications marked as read."}
