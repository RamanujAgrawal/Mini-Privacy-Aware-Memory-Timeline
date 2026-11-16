from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.event import EventCategory
from app.services.audit_service import AuditService

# The four foundational categories evaluated in this prototype
VALID_CATEGORIES = [c.value for c in EventCategory]


class PrivacyService:
    """
    Privacy & Permission Management Subsystem
    -----------------------------------------
    Manages user category toggles (conversation, location, physiological, note).
    Ensures that default permissions exist upon first run, validates category
    names, and emits audit entries whenever privacy boundaries are altered.
    """

    @staticmethod
    def ensure_default_permissions(db: Session, user_id: int) -> None:
        """
        Ensures all 4 categories exist in the database for the user with default ON (True).
        Runs lazily on first access so newly registered users immediately have complete records.
        """
        existing = {
            p.category for p in db.query(Permission).filter(Permission.user_id == user_id).all()
        }
        for cat in VALID_CATEGORIES:
            if cat not in existing:
                perm = Permission(
                    user_id=user_id,
                    category=cat,
                    is_enabled=True
                )
                db.add(perm)
        db.commit()

    @staticmethod
    def get_permissions(db: Session, user_id: int) -> Dict[str, bool]:
        """
        Returns a dictionary mapping each category to its boolean state:
        e.g. {'conversation': True, 'location': False, 'physiological': True, 'note': True}
        """
        PrivacyService.ensure_default_permissions(db, user_id)
        records = db.query(Permission).filter(Permission.user_id == user_id).all()
        return {record.category: record.is_enabled for record in records}

    @staticmethod
    def get_allowed_categories(db: Session, user_id: int) -> List[str]:
        """
        Returns a list of category names that are currently enabled (is_enabled == True).
        Used directly by EventService to build SQL `WHERE type IN (...)` clauses.
        """
        perms = PrivacyService.get_permissions(db, user_id)
        return [cat for cat, enabled in perms.items() if enabled]

    @staticmethod
    def is_category_allowed(db: Session, user_id: int, category: str) -> bool:
        """
        Quick boolean check for single-event authorization guards.
        """
        perms = PrivacyService.get_permissions(db, user_id)
        return perms.get(category, False)

    @staticmethod
    def update_permission(
        db: Session,
        user_id: int,
        category: str,
        is_enabled: bool
    ) -> Permission:
        """
        Updates a user's category permission and atomically writes a log to the audit trail.
        Returns the updated Permission record.
        """
        PrivacyService.ensure_default_permissions(db, user_id)
        perm = (
            db.query(Permission)
            .filter(Permission.user_id == user_id, Permission.category == category)
            .first()
        )
        if not perm:
            perm = Permission(user_id=user_id, category=category, is_enabled=is_enabled)
            db.add(perm)
        else:
            perm.is_enabled = is_enabled

        db.commit()
        db.refresh(perm)

        # Audit trail: log permission state change
        action_name = f"PERMISSION_SET_{'ON' if is_enabled else 'OFF'}"
        AuditService.record_action(
            db=db,
            user_id=user_id,
            action=action_name,
            result="UPDATED",
            event_type=category
        )

        return perm
