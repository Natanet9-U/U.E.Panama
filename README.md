# 🚀 Proyecto U.E. PANAMA

## 📌 Descripción

Proyecto web full stack usando:

* Backend con Django (API REST)
* Frontend con React
* Base de datos PostgreSQL

---

## 🧱 Tecnologías

* Python / Django
* Django REST Framework
* React
* PostgreSQL

---

## ⚙️ Instalación

### 🔹 Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate 

pip install -r ../requirements.txt
python manage.py migrate
python manage.py seed_school_data
python manage.py runserver
```

El comando `seed_school_data` carga datos de ejemplo del colegio para 2026: director, secretaria, docentes, áreas, grados, períodos, dimensiones de evaluación, tutores, estudiantes, cursos, horarios, notas y asistencias.

---

### 🔹 Frontend

```bash
cd frontend
npm install
npm start
```

---

## 📂 Estructura

```
mi_proyecto/
│
├── backend/
├── frontend/
├── requirements.txt
└── README.md
```