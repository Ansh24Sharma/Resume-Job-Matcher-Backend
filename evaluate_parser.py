import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from preprocess import clean_text

def create_similarity_features(resume_text, job_text, vectorizer):
    """Create features based on text similarity between resume and job"""
    # Transform both texts
    resume_vec = vectorizer.transform([resume_text])
    job_vec = vectorizer.transform([job_text])
    
    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity(resume_vec, job_vec)[0][0]
    
    # Create feature vector (you can add more features here)
    features = [similarity]
    return features

def evaluate_parser(resume_csv="data/resume_dataset.csv", job_csv="data/job_dataset.csv"):
    print("📖 Loading data...")
    resumes = pd.read_csv(resume_csv)
    jobs = pd.read_csv(job_csv)
    
    # Prepare data
    features = []
    labels = []
    
    print("🔄 Processing resume-job pairs...")
    for idx, row in resumes.iterrows():
        # Clean resume text
        resume_text = f"{row['Career_objective']} {row['Skills']} {row['Experience_requirement']} {row['Education']}"
        resume_text = clean_text(resume_text)
        
        # Create positive example (matching job)
        pos_jobs = jobs[jobs['Skills'].str.contains(str(row['Skills']).split(",")[0], case=False, na=False)]
        if not pos_jobs.empty:
            job = pos_jobs.sample(1, random_state=idx).iloc[0]
            job_text = f"{job['Responsibilities']} {job['Skills']} {job['Education']}"
            job_text = clean_text(job_text)
            
            # We'll add features after vectorization
            features.append((resume_text, job_text))
            labels.append(1)  # Match
        
        # Create negative example (random job)
        job = jobs.sample(1, random_state=idx+42).iloc[0]
        job_text = f"{job['Responsibilities']} {job['Skills']} {job['Education']}"
        job_text = clean_text(job_text)
        
        features.append((resume_text, job_text))
        labels.append(0)  # No match
    
    print(f"✅ Created {len(features)} resume-job pairs")
    
    # Prepare all texts for vectorization
    all_texts = []
    for resume_text, job_text in features:
        all_texts.extend([resume_text, job_text])
    
    # Create and fit vectorizer
    print("🔤 Creating text features...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    vectorizer.fit(all_texts)
    
    # Create feature matrix
    X = []
    for resume_text, job_text in features:
        feature_vector = create_similarity_features(resume_text, job_text, vectorizer)
        X.append(feature_vector)
    
    # Convert to proper format
    X = pd.DataFrame(X, columns=['cosine_similarity'])
    y = labels
    
    # Split data into training and testing
    print("📊 Splitting data for training and testing...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create and train classifier
    print("🤖 Training classifier...")
    classifier = LogisticRegression(random_state=42)
    classifier.fit(X_train, y_train)
    
    # Make predictions
    print("🔮 Making predictions...")
    y_pred = classifier.predict(X_test)
    
    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    
    # Print results
    print("\n" + "="*50)
    print("📊 PARSER EVALUATION RESULTS")
    print("="*50)
    print(f"🎯 Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    print("\n📈 Detailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Match', 'Match']))
    
    # Show feature importance
    print("\n🔍 Feature Importance:")
    for i, feature_name in enumerate(['cosine_similarity']):
        importance = abs(classifier.coef_[0][i])
        print(f"   {feature_name}: {importance:.3f}")
    
    return accuracy, classifier

def predict_match(resume_text, job_text, classifier, vectorizer):
    """Predict if a resume matches a job using the trained classifier"""
    # Clean texts
    resume_text = clean_text(resume_text)
    job_text = clean_text(job_text)
    
    # Create features
    features = create_similarity_features(resume_text, job_text, vectorizer)
    features_df = pd.DataFrame([features], columns=['cosine_similarity'])
    
    # Make prediction
    prediction = classifier.predict(features_df)[0]
    probability = classifier.predict_proba(features_df)[0][1]  # Probability of match
    
    return prediction, probability

if __name__ == "__main__":
    print("🚀 Starting Resume-Job Parser Evaluation")
    print("-" * 40)
    
    try:
        accuracy, trained_classifier = evaluate_parser()
        print(f"\n✅ Evaluation completed successfully!")
        print(f"🏆 Final Accuracy: {accuracy:.3f}")
        
    except FileNotFoundError:
        print("❌ Error: Could not find the data files.")
        print("   Make sure 'data/resume_dataset.csv' and 'data/job_dataset.csv' exist.")
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")