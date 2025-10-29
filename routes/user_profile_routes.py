from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from auth import get_current_user
from service.user_profiles_service import (
    get_user_profile, 
    update_user_profile, 
    get_all_user_profiles
)
from models.user_profile_models import (
    UserProfileResponse, 
    UserProfileUpdate, 
    UserProfileSummary
)

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/myProfile", response_model=UserProfileResponse)
async def get_my_profile(user: tuple = Depends(get_current_user)):
    """Get current user's profile"""
    try:

        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        
        user_id = user_dict.get("user_id")
        print(f"[INFO] Fetching profile for user_id: {user_id}")
        profile = get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User profile not found"
            )
            
        return profile
    except Exception as e:
        print(f"[ERROR] Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/update", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate, 
    user: tuple = Depends(get_current_user)
):
    """Update current user's profile and calculate completion percentage"""
    try:
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        
        user_id = user_dict.get("user_id")
        
        # Convert to dict and remove None values
        update_data = profile_update.dict(exclude_none=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Get current profile to merge with updates
        current_profile = get_user_profile(user_id)
        if not current_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User profile not found"
            )
        
        # Merge current profile with updates for completion calculation
        merged_profile = {**current_profile, **update_data}
        
        # Calculate completion percentage
        required_fields = ["name", "email", "skills", "experience", "education", "location"]
        completed_fields = 0
        
        for field in required_fields:
            if field in ["skills", "experience", "education"]:
                if merged_profile.get(field) and len(merged_profile.get(field, [])) > 0:
                    completed_fields += 1
            else:
                if merged_profile.get(field):
                    completed_fields += 1
        
        completion_percentage = int((completed_fields / len(required_fields)) * 100)
        
        # Add completion percentage to update data
        update_data["completion_percentage"] = completion_percentage
        
        # Update profile with completion percentage
        success = update_user_profile(user_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        # Return updated profile
        updated_profile = get_user_profile(user_id)
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to update profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.get("/all", response_model=List[UserProfileSummary])
async def get_all_profiles(user: tuple = Depends(get_current_user)):
    """Get all user profiles summary (admin only)"""
    try:
        # Check if current user is admin
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        
        user_role = user_dict.get("user_role")
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        profiles = get_all_user_profiles()
        
        # Convert to summary format
        profile_summaries = []
        for profile in profiles:
            profile_summaries.append({
                "id": profile["id"],
                "user_id": profile["user_id"],
                "username": profile["username"],
                "name": profile["name"],
                "email": profile["email"],
                "location": profile["location"],
                "skills_count": len(profile["skills"]) if profile["skills"] else 0,
                "experience_count": len(profile["experience"]) if profile["experience"] else 0,
                "profile_completed": profile["profile_completed"],
                "resume_uploaded": bool(profile["resume_filename"]),
                "last_updated": profile["updated_at"]
            })
        
        return profile_summaries
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get all profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profiles"
        )