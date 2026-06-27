from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileUpsert


def upsert_profile(db: Session, user: User, data: ProfileUpsert) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile:
        profile.first_name = data.first_name
        profile.last_name = data.last_name
        profile.phone_number = data.phone_number
        profile.avatar_url = data.avatar_url
    else:
        profile = Profile(
            user_id=user.id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            avatar_url=data.avatar_url,
        )
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
