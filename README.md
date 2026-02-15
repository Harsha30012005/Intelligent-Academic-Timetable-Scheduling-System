# 🎓 Intelligent Academic Timetable Scheduling System

## 🚀 Overview

The **Intelligent Academic Timetable Scheduling System** is an AI-driven deliberative planning agent designed to automatically generate optimized, conflict-free academic timetables for universities and educational institutions.

The system integrates:

- Constraint Satisfaction (CSP)
- Optimization Techniques
- Hybrid AI Planning Strategies

to handle complex academic scheduling constraints efficiently.

---

## 🎯 Problem Statement

Academic timetable generation involves multiple interdependent constraints:

- Teacher availability  
- Classroom capacity  
- Laboratory requirements  
- Batch overlaps  
- Faculty workload limits  
- Time slot balancing  
- Resource utilization  

Manual scheduling often leads to:

- Conflicts  
- Inefficient resource usage  
- Imbalanced workload  
- Human errors  
- Time-consuming adjustments  

This system automates and optimizes the entire process.

---

## 🧠 Core Features

### ✅ Hard Constraint Handling
- No teacher clashes  
- No batch clashes  
- Lab courses assigned only to lab rooms  
- Teacher daily workload limit enforcement  
- Room availability validation  

### ⚙ Optimization Engine
- Day distribution balancing  
- Teacher load fairness  
- Room utilization balancing  
- Hybrid CSP + Optimization approach  

### 📊 Advanced AI Evaluation Metrics
- Room Utilization Percentage  
- Teacher Fairness Score  
- Day Balance Score  
- Global Efficiency Score  

### 🔍 Coverage Validation
- Required vs Scheduled hours check  
- Missing course detection  

### ⚠ Feasibility Analysis
- Weekly capacity validation  
- Lab capacity validation  
- Teacher workload feasibility check  
- Batch weekly load feasibility  

---

## 🖥 System Architecture

```
Flask Web App
      ↓
Scheduling Engine (CSP + Optimizer + Hybrid)
      ↓
Evaluation & Validation Module
      ↓
Visualization Dashboard (Charts + Metrics)
```

---

## 📂 Project Structure

```
Intelligent_Timetable_Agent/
│
├── app.py
├── engine.py
├── templates/
│   ├── landing.html
│   ├── dashboard.html
│   ├── analytics.html
│   ├── coverage.html
│
├── static/
├── requirements.txt
└── README.md
```

---

## 🛠 Technologies Used

- Python  
- Flask  
- Pandas  
- Chart.js  
- Bootstrap 5  
- ReportLab (PDF Export)  

---

## 📈 AI Evaluation Metrics

| Metric | Description |
|--------|------------|
| Room Utilization | Percentage of total room usage |
| Teacher Fairness | Workload distribution score |
| Day Balance | Slot distribution stability |
| Global Efficiency | Weighted overall performance score |

---

## 📥 How to Run Locally

```bash
git clone https://github.com/yourusername/Intelligent-Academic-Timetable-Scheduling-System.git
cd Intelligent-Academic-Timetable-Scheduling-System
pip install -r requirements.txt
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

## 🌍 Future Enhancements

- Admin panel for manual data entry  
- Database integration  
- Role-based authentication  
- Cloud deployment  
- Multi-institution support  
- AI-based auto-weight tuning  

---

## 👨‍💻 Developed By

Harsha  
B.Tech AI Academic Project  
AI-Based Deliberative Planning Agent System  

---

## 📜 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

© 2026 Harsha Vardhan Ghadge

---

⭐ If you find this project useful, consider giving it a star!
