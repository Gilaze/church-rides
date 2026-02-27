Check out the website here:
https://church-rides-gilaze7393-of35ddsq.leapcell.dev


My blog of this project:

# 🚐 Church Transportation System
**A streamlined, automated solution for church shuttle management.**

---

## 🚀 The Application
Over winter break, I created and deployed an online transportation system for my church using **Python, SQL, Flask**, and **Leapcell**. 

A passenger, after creating a profile, can easily add themselves to a listed pickup location with a simple click. The website displays the entire transportation list for the week in **real-time**, and administrators have access to a metric dashboard to track attendance and send confirmation emails.

---

## 📉 The Before
The church operates a shuttle system with three vans for students without cars. Previously, the process was inefficient:
* **Manual Entry:** Students had to fill out a long Google Form every single week.
* **Repetition:** The form required the same information (name, phone, dorm) repeatedly.
* **Missed Deadlines:** If the Friday night deadline was missed, students had to take the bus (which had inconvenient hours).

> **The Problem:** When the barrier to entry is high, attendance drops. I embarked on this project to create a simple, efficient solution to increase church attendance.

---

## 🛠 The System
The system is built upon three core pillars: **Users**, **Rides**, and **Automated Tasks**.

### 👤 Users
#### User Accounts
I implemented user accounts to store personal information persistently. Unlike a static form, a function passes saved, mandatory information to drivers with a single click.
* **Security:** Built using `Flask-login` and `Werkzeug` for password encryption.
* **Database:** Credentials are safely stored in an online SQL database.
* **Convenience:** Includes a "Remember Me" feature for returning users.

#### User Types
| Role | Permissions |
| :--- | :--- |
| **Passenger** | Can join a ride with one click. |
| **Driver** | Can create/remove pickup locations and set their total passenger capacity. |
| **Admin** | Access to the metric dashboard, master passenger list (PDF), and bulk email tools. |

---

### 📍 Rides
I shifted the logic from "Vehicle-based" to **"Pickup Location-based"** to resolve scheduling confusion.
* **The Logic:** Since drivers rotate weekly, passengers shouldn't need to know *who* is driving, only *where* they are being picked up.
* **Driver Capacity:** A driver's capacity applies to the **accumulated sum** of passengers across all locations they are assigned to, rather than a per-stop limit.

---

### 🤖 Automated Tasks
To minimize manual labor, I utilized **GitHub Actions** for site maintenance:

1. **Weekly Reset:** Every Monday at 12:00 AM, a script clears all weekly pickup locations and passengers (unless the "Remember Vehicle" box is checked).
2. **Health Checks:** A script pings the website every 15 minutes. If it fails 3 consecutive times, it detects an outage.
3. **Emergency Backup:** In the event of an outage, an automated email is sent to admins with the most recent transportation list attached as a PDF.

---

## 🔗 Relation to Fastopp
This project allowed me to scale skills learned during my time at Fastopp:
* **Object Relational Mapping (ORM):** Used Python to translate SQL queries to Leapcell, allowing for dynamic item/location additions.
* **Object-Oriented Programming (OOP):** Developed robust `User` and `PickupLocation` classes with distinct attributes.
* **Scalability:** Learned that real-world applications require more than just a "core function"—they need auth systems, superuser permissions, and error handling.

---

## 💡 Concluding Thoughts
Building this project was a rewarding experience that merged academic knowledge with real-world impact. Seeing actual users on the platform and knowing it facilitates community attendance is the ultimate goal of software engineering.
