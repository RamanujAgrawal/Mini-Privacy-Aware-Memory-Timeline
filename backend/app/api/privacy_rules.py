from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user_id
from app.models.privacy_rule import PrivacyRule
from app.schemas.privacy_rule import PrivacyRuleCreate, PrivacyRuleResponse, PrivacyRuleListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/privacy-rules", tags=["Granular Privacy Rules"])


@router.get("", response_model=PrivacyRuleListResponse)
def list_privacy_rules(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    List all active granular privacy rules configured for the authenticated user.
    """
    rules = db.query(PrivacyRule).filter(PrivacyRule.user_id == user_id).order_by(PrivacyRule.id.desc()).all()
    return PrivacyRuleListResponse(
        items=[PrivacyRuleResponse.model_validate(r) for r in rules],
        total=len(rules)
    )


@router.post("", response_model=PrivacyRuleResponse, status_code=status.HTTP_201_CREATED)
def create_privacy_rule(
    rule_in: PrivacyRuleCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Create a new granular privacy rule (keyword redaction or event drop action).
    """
    category_val = rule_in.category.value if hasattr(rule_in.category, "value") else str(rule_in.category)
    rule = PrivacyRule(
        user_id=user_id,
        category=category_val,
        rule_type=rule_in.rule_type,
        pattern=rule_in.pattern.strip(),
        action=rule_in.action.strip().lower(),
        is_enabled=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    AuditService.record_action(
        db=db,
        user_id=user_id,
        action="CREATE_PRIVACY_RULE",
        result="CREATED",
        event_type=category_val
    )
    return PrivacyRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_200_OK)
def delete_privacy_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Delete a specific granular privacy rule.
    """
    rule = db.query(PrivacyRule).filter(
        PrivacyRule.id == rule_id,
        PrivacyRule.user_id == user_id
    ).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Privacy rule #{rule_id} not found."
        )

    category = rule.category
    db.delete(rule)
    db.commit()

    AuditService.record_action(
        db=db,
        user_id=user_id,
        action="DELETE_PRIVACY_RULE",
        result="DELETED",
        event_type=category
    )
    return {"message": f"Privacy rule #{rule_id} deleted successfully."}
