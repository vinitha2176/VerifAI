# Employment Scam Aegean Dataset (EMSCAD)

## 1. Dataset Overview

The dataset used for training and evaluating VerifAI's machine learning model is the **Employment Scam Aegean Dataset (EMSCAD)**.

- **Primary Research Paper**: 
  Vidros, S., Miniotas, C., Pedemonte, E., & Kolias, C. (2017). *A Method for the In-Depth, Real-Time Detection of Scam Job Advertisements*. Future Internet, 9(1), 6.
  URL: [https://www.mdpi.com/1999-5903/9/1/6](https://www.mdpi.com/1999-5903/9/1/6)
- **Primary Source**: Laboratory of Information & Communication Systems Security (Info-Sec-Lab), University of the Aegean, Greece.
- **Kaggle Distribution**: [Real / Fake Job Posting Prediction](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0) / Public Domain.

## 2. Dataset Structure

- **Filename**: `fake_job_postings.csv`
- **Total Records**: 17,880 job advertisements
- **Target Feature**: `fraudulent`
  - `0`: Legitimate job advertisement (17,014 records, ~95.16%)
  - `1`: Fraudulent job advertisement (866 records, ~4.84%)
- **Imbalance Ratio**: Approximately 19.6 : 1

### Feature Columns:
1. `job_id`: Unique identification number
2. `title`: Job advertisement title
3. `location`: Geographical location of the posting (Country, State, City)
4. `department`: Corporate department
5. `salary_range`: Specified salary or compensation range
6. `company_profile`: Corporate introductory text / background
7. `description`: Core job description and role details
8. `requirements`: Candidate qualifications and experience required
9. `benefits`: Perks, healthcare, or employee benefits offered
10. `telecommuting`: Whether remote work / telecommuting is permitted (binary)
11. `has_company_logo`: Whether an official company logo is present (binary)
12. `has_questions`: Whether screening questions are present (binary)
13. `employment_type`: Full-time, Part-time, Contract, etc.
14. `required_experience`: Internship, Entry level, Mid-Senior, Executive, etc.
15. `required_education`: High school, Bachelor's, Master's, etc.
16. `industry`: Industry sector (e.g., Information Technology, Oil & Energy)
17. `function`: Job function (e.g., Engineering, Sales, Administrative)
18. `fraudulent`: Target binary indicator (0 for legitimate, 1 for fraudulent)

## 3. Usage in VerifAI

VerifAI concatenates and standardizes the informative textual features (`title`, `company_profile`, `description`, `requirements`, and `benefits`) into a unified corpus per sample. This text undergoes cleaning, HTML tag removal, whitespace normalization, and TF-IDF n-gram vectorization before passing into stratified training pipelines.
