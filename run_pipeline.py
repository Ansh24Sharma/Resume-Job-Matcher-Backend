from service.db import init_db
from sample_loader import insert_sample_data
from service.recommendation_service import run_matcher, get_top_recommendations
from evaluate_parser import evaluate_parser   
 
 
def run_pipeline():
    print("🔄 Step 1: Initializing database...")
    init_db()
    print("✅ Database initialized.")
 
    # print("🔄 Step 2: Inserting Data (resumes + jobs)...")
    # insert_sample_data(limit_resumes=100, limit_jobs=100)  
    # print("✅ Data inserted.")
 
    print("🔄 Step 2: Running matcher...")
    run_matcher()
    print("✅ Matching completed.")
 
    # Pick a test resume
    test_resume_id = 3
    print(f"\n📌 Top 5 Job Recommendations for Resume {test_resume_id}:")
    recommendations = get_top_recommendations(test_resume_id, top_n=5)
 
    if not recommendations:
        print("⚠️ No recommendations found. Make sure data is loaded properly.")
    else:
        for job in recommendations:
            print(f"- {job['title']} (Score: {job['final_score']:.2f}) | "
                  f"Skills: {job['skill_score']:.2f}, "
                  f"Edu: {job['education_score']}, "
                  f"Exp: {job['experience_score']}")
 
    # 🔄 Step 4: Evaluate parser accuracy
    print("\n🔄 Step 4: Evaluating parser accuracy with RandomForestClassifier...")
    evaluate_parser()
    print("✅ Parser evaluation completed.")
 
 
if __name__ == "__main__":
    run_pipeline()
 