"""数据导入 API"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from src.data_access.parsers.resume_parser import ResumeParser
from src.data_access.parsers.jd_parser import JDParser
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.job_repository import job_repository
from src.presentation.api.deps import get_current_user, get_db

router = APIRouter()


@router.post("/resume")
async def import_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    导入简历（PDF 或 DOCX）
    """
    parser = ResumeParser()

    try:
        content = await file.read()
        result = parser.parse(content, file.filename)

        resume = resume_repository.create(db, {
            "user_id": current_user.id,
            "title": result.name or "未命名简历",
            "original_file_path": file.filename or "",
            "file_name": file.filename or "unknown",
            "file_type": file.filename.split(".")[-1].lower() if file.filename else "unknown",
            "resume_text": result.raw_text,
            "processed_content": result.raw_text,
        })

        return {
            "success": True,
            "resume_id": resume.id,
            "parsed": {
                "name": result.name,
                "education": result.education,
                "skills": result.skills,
                "experience": result.experience,
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/jds")
async def import_jds(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    批量导入 JD（CSV 或 Excel）
    """
    parser = JDParser()

    try:
        content = await file.read()
        results = parser.parse_file(content, file.filename)

        imported = 0
        failed = 0
        errors = []

        for idx, jd_data in enumerate(results):
            try:
                job_repository.create(db, {
                    "title": jd_data.title,
                    "company": jd_data.company,
                    "description": jd_data.description,
                    "requirements": jd_data.requirements,
                    "location": jd_data.location or "",
                    "salary": jd_data.salary,
                    "source": "import",
                })
                imported += 1
            except Exception as e:
                failed += 1
                errors.append(f"Row {idx + 1}: Failed to import '{jd_data.title}' - {str(e)}")

        return {
            "success": True,
            "total": len(results),
            "imported": imported,
            "failed": failed,
            "errors": errors,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )