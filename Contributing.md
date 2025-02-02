# Contributing to Timely

Thank you for your interest in contributing to **Timely**! 🎉  
We appreciate your efforts in making this project better. Please follow the guidelines below to ensure smooth collaboration while adhering to the licensing terms.

---

## 🔹 Definitions  
- **Author:** Ketan Vishwakarma ([Ketan-coder](https://github.com/Ketan-coder))  


---

## 🚨 **Important Project Guidelines**

1. **Author's Approval Required**: All contributions and changes to the project are subject to **approval by the Author (Ketan Vishwakarma)**. The Author has the final say on whether changes will be merged or not.
2. **Non-Commercial Use**: This project is licensed under terms that prevent its **marketing or selling** in any form. Contributors are prohibited from introducing in-app transactions or commercializing the software in any way.
3. **Code of Conduct**: All contributions must follow the **Code of Conduct** by being respectful and inclusive. Discussions and contributions should promote a positive and collaborative environment.
4. **No In-App Transactions**: Any modifications, especially those involving monetization (e.g., in-app purchases), will not be accepted unless approved by the Author.
5. **Future Changes**: While this project will evolve and grow, the core functionality and main features will remain unchanged unless decided by the Author. Any major changes will require careful consideration and approval from the Author.
6. **Testing Before Commiting**: Please do **not** commit directly to the main branch. Instead, create a new branch and commit your changes there. This allows us to review and test your code before merging it into the main branch. Also Test your changes before submitting a PR.

---

## 📌 How to Contribute

### 1️⃣ Fork & Clone the Repository
1. Fork the repository by clicking the "Fork" button on GitHub.
2. Clone your fork to your local machine:
   ```bash
   git clone https://github.com/Ketan-coder/NoteTakingApp.git
   ```
3. Navigate to the project directory:
   ```bash
   cd NoteTakingApp/Timely
   ```
4. Create a new branch:
   ```bash
   git checkout -b feature-branch
   ```

---

### 2️⃣ Install Dependencies & Set Up Project
1. Create a virtual environment:
   ```bash
   python -m venv env
   ```
2. Activate the environment:
   ```bash
   source env/bin/activate  # macOS/Linux
   env\Scripts\activate      # Windows
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply migrations:
   ```bash
   python manage.py migrate
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

---

### 3️⃣ Make & Submit Changes
1. Make your changes following Django best practices.
2. Stage your changes:
   ```bash
   git add .
   ```
3. Commit your changes:
   ```bash
   git commit -m "Added feature XYZ"
   ```
4. Push to your fork:
   ```bash
   git push origin feature-branch
   ```
5. Open a **Pull Request (PR)** on the main repository.

---

## ✅ Contribution Guidelines
- Prefered Changes/Features are listed in Timely/changes.md file.
- Follow PEP8 coding standards.
- Ensure your code is well-documented.
- Write meaningful commit messages.
- Test your changes before submitting a PR.
- Be respectful and inclusive in discussions.

---

## 📌 Reporting Issues
If you find any bugs or have feature requests, please [open an issue](https://github.com/Ketan-coder/NoteTakingApp.git/issues).

