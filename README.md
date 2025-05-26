# 🧑‍🌾 Farmers Marketplace – Direct Market Access

A web-based platform to directly connect farmers and customers, eliminating middlemen. The platform includes separate dashboards for **farmers**, **customers**, and **admins** to manage product listings, certifications, orders, and verifications efficiently.

## 🔗 Live Demo

Deployed on [Render](https://render.com)

🌐 **[Click here to view the deployed app](https://adl-lab-1.onrender.com/)**  
Hosted on [Render](https://render.com)

---




## 📌 Features

### 👨‍🌾 Farmer Dashboard
- Signup/Login as a farmer
- Add and manage products (name, price, quantity, image)
- Upload certification documents (e.g., organic, FSSAI)
- View certificate verification status

### 🛒 Customer Dashboard
- Signup/Login as a customer
- Browse and search available products
- Add products to wishlist
- Place orders directly with farmers
- Rate and review products

### 🛡️ Admin Dashboard
- View certificates uploaded by farmers
- Approve or reject certification requests
- Manage farmer/customer user accounts

---

## 🛠️ Tech Stack

| Layer       | Technology                  |
|-------------|-----------------------------|
| Backend     | Python Flask                |
| Frontend    | HTML, CSS, JavaScript       |
| Database    | PostgreSQL                  |
| Deployment  | Render                      |

---

## 📁 Project Structure

adl_lab/
├── app.py # Main application file
├── config.py # Configuration settings
├── models.py # Database models
├── requirements.txt # Python dependencies
├── Procfile # For deployment on Render
├── instance/ # Configuration and DB instance
├── static/ # Static files (CSS, JS, images)
├── templates/ # HTML templates
├── .github/workflows/ # GitHub Actions workflows
└── README.md # Project overview


---

## 🚀 Getting Started (Local Setup)

1. **Clone the repository**

```bash
git clone https://github.com/<your-username>/adl_lab.git
cd adl_lab
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=postgresql://<username>:<password>@localhost/<dbname>
SECRET_KEY=your_secret_key
flask run
