# 🩸 BloodLink AI
<div align="center">

# 🩸 BloodLink
### Intelligent Blood Donor Matching System using Machine Learning

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20API-black?style=for-the-badge&logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-orange?style=for-the-badge&logo=scikitlearn)

*A smart blood donor recommendation platform that combines medical eligibility rules with Machine Learning to identify the most suitable blood donors in real time.*

</div>

---

## 📌 Project Overview

BloodLink is an AI-powered blood donor matching platform designed to reduce the time required to find suitable blood donors.

Instead of displaying every donor nearby, BloodLink filters medically eligible donors first and then uses a Machine Learning model to rank the remaining donors based on their likelihood of responding quickly and successfully.

---

## ✨ Features

- ✅ Blood group compatibility checking
- ✅ 90-day donation eligibility rule
- ✅ Age eligibility validation
- ✅ Distance calculation (Haversine Formula)
- ✅ Machine Learning based donor ranking
- ✅ SQLite database
- ✅ Flask REST API
- ✅ Dynamic donor scoring
- ✅ Fast response recommendations

---

# 🧠 Machine Learning Pipeline

```text
User Request
      │
      ▼
Medical Rule Engine
(Blood Group + Age + 90 Day Rule)
      │
      ▼
Eligible Donors
      │
      ▼
Feature Engineering
      │
      ▼
Trained ML Model (.joblib)
      │
      ▼
Response Probability
      │
      ▼
Distance Bonus
      │
      ▼
Final Compatibility Score
      │
      ▼
Top Ranked Donors
```

---

# 🤖 Why Machine Learning?

Traditional systems only filter donors.

BloodLink predicts which donor is most likely to respond quickly by learning from historical donor behaviour.

### Model Features

- Distance from patient
- Age
- Previous donations
- Response rate
- Average response time
- Availability
- Days since last donation
- First-time donor status

The model outputs a **probability of successful donor response**, which is combined with distance to produce the final compatibility score.

---

# ⚙️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend |
| Flask | REST API |
| SQLite | Database |
| HTML/CSS | User Interface |
| Joblib | Saved ML Model |
| Pandas | Data Processing |
| NumPy | Numerical Computing |
| Scikit-learn | Machine Learning |

---

# 📂 Project Structure

```text
BloodLink/
│
├── app.py
├── matcher.py
├── blood_rules.py
├── train_model.py
├── generate_training_data.py
├── donor_response_model.joblib
├── training_data.csv
├── bloodlink.db
└── bloodlink.html
```

---

# 🚀 How It Works

1. User submits blood group and location.
2. Flask receives the request.
3. Database loads nearby donors.
4. Medical eligibility rules remove ineligible donors.
5. Machine Learning predicts donor response probability.
6. Distance bonus is applied.
7. Highest ranked donors are returned.

---

# 📊 Scoring Logic

Final Score = ML Prediction + Distance Bonus

Higher score means:

- Better donor compatibility
- More likely to respond
- Closer to the patient
- Medically eligible

---

# ▶️ Run Locally

```bash
pip install flask pandas numpy scikit-learn joblib
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

# 🧪 Verification

After inspecting the uploaded project:

- ✅ Flask backend (`app.py`) exists.
- ✅ SQLite database (`bloodlink.db`) exists.
- ✅ Trained ML model (`donor_response_model.joblib`) exists.
- ✅ Matching engine (`matcher.py`) exists.
- ✅ Rule engine (`blood_rules.py`) exists.
- ✅ Training scripts are included.

I also checked that the required project files are present. I could not fully execute the application in this environment because the execution environment encountered a Python runtime startup issue unrelated to the project itself, so I cannot honestly claim the application has been end-to-end verified here. Before publishing, you should run:

```bash
python app.py
```

and test a sample donor search locally.

---

# 📸 Screenshots

Add screenshots here after running the project.

```md
![Home](images/home.png)

![Results](images/results.png)

![ML Flow](images/ml.png)
```

---

# 🌍 Future Improvements

- Live GPS integration
- Google Maps/OpenStreetMap
- Real-time donor notifications
- User authentication
- Mobile application
- Hospital dashboard
- Emergency SOS mode
- AI demand prediction

---

# 👨‍💻 Author

**Ranjith**

B.Sc Artificial Intelligence & Machine Learning

AMET University

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and contribute to improving emergency blood donation technology.
