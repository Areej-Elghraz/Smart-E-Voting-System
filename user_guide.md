# Smart E-Voting System - User Guide

This guide explains how to use all the features of the Smart E-Voting system, from both the Administrator and Voter perspectives.

---

## 1. Getting Started

1. **Start the Server:** Open your terminal in the project folder and run:
   ```bash
   python run.py
   ```
2. **Access the App:** Open your web browser and go to `http://127.0.0.1:5000`.

---

## 2. Administrator Guide

The Administrator is responsible for setting up the environment, managing organizations, and monitoring system security.

### 2.1 First-time Admin Login
1. On the homepage, click **Login**.
2. Enter the default admin credentials:
   - **Username:** `admin` (or `admin@evoting.com`)
   - **Password:** `admin123`
3. **OTP Bypass:** Admins automatically bypass the OTP step for faster access.
4. You will be redirected to the **Admin Dashboard** where you can see high-level statistics, an Election Status Pie Chart, and recent system alerts.

### 2.2 Smart Analytics & Security Dashboard
1. Click on **Analytics & Risk** in the top navigation bar.
2. **Real-Time Engagement Monitoring (IOB):** 
   - View registration completion rates and identify bottlenecks (where users get stuck).
   - Track average time taken to vote.
3. **Candidate Engagement Monitoring:**
   - Track **Profile Views** for each candidate.
   - View the **Interest Gauge** to see which candidates are attracting the most attention.
4. **Participation Prediction:**
   - The system predicts **Expected Turnout** and **Peak Voting Times** based on current voting velocity.
5. **Behavioral Security:**
   - View **Risky Sessions** flagged by the AI based on unusual behavior (e.g., new IP, rapid refreshes, late-night activity).
   - Each session is assigned a **Smart Risk Score** from 0 to 100.
6. **Account Locking:** Monitor users who have been locked out due to excessive failed login attempts (5+).

### 2.3 Managing Users
1. Click on **Users** to view, promote (Voter to Admin), or delete users.
2. **Performance Tip:** This page is cached for performance. Any changes will instantly refresh the cache.

### 2.4 Managing Organizations
1. Click on **Organizations** to create, update, or delete groups.
2. **Access Codes:** Organizations can have codes that allow voters to join autonomously.
3. **Member Management:** Manually add or remove members from specific organizations.

### 2.5 Managing Elections & Automated Scheduling
1. Click on **Elections** in the top navigation.
2. **Automated Scheduling:**
   - When creating or updating an election, set a **Start Time** and **End Time**.
   - The system will automatically transition the status from `upcoming` to `active` when the start time is reached, and to `closed` when it ends.
3. **Election Topics:**
   - Admins can define specific topics for an election.
   - **AI-Extracted Themes:** The system also automatically identifies key themes from candidate manifestos using TF-IDF.
4. **Candidate Management:** 
   - Expand an election to add candidates.
   - Provide a detailed **Manifesto/Description** and **Keywords**. This data powers the AI matching engine.
5. **Results:** View real-time tallies and visual bar charts.

### 2.6 Audit Log
1. Tracks all system actions, including login attempts, voting events, and security alerts.

---

## 3. Voter Guide

Voters use the system to cast secure, anonymous ballots.

### 3.1 Registration & Login
1. **Register:** Provide Username, Email, unique ID Card, and Password.
2. **First Login (OTP):** On your first successful login, you must enter a 6-digit OTP sent to your email.
3. **OTP Skipping:** After your first successful verification, future logins from the same account will bypass the OTP step to save time.
4. **Security Locking:** If you enter the wrong password 5 times, your account will be locked for security. Contact an admin to unlock it.

### 3.2 Joining Organizations & Candidate Profiles
1. **Dashboard:** View organizations you belong to and active elections.
2. **Candidate Profiles:** On the election page, click **View Profile** to read a candidate's full manifesto. Your visit is recorded anonymously as an engagement metric.

### 3.3 Smart Recommendations & AI NLP Matching
1. **Topic Selection:** On the election page, select from **Predefined Topics** (by admin) or **AI-Extracted Themes** (generated from candidate manifestos).
2. **Custom Interests:** You can also type in specific issues you care about.
3. **AI NLP Matching:** The system uses **TF-IDF Vectorization** and **Cosine Similarity** to compare your selected topics against all candidate programs.
4. **Match Percentage:** View a precise percentage score for each candidate, showing who best represents your interests.

### 3.4 Secure Voting
1. **Casting a Vote:** Select your candidate and submit your anonymous vote.
2. **Blockchain Ledger:** Every vote is converted into a secure block and linked to the previous one, ensuring your vote can never be altered or deleted.
3. **Anonymity:** The system records *that* you voted to prevent double-voting, but separates this from *who* you voted for.

---

## 4. Performance & Technology
- **Caching Engine:** Uses `Flask-Caching` for instant load times across the dashboard and analytics.
- **AI Security:** Real-time anomaly detection using `Isolation Forest` algorithms.
- **NLP Engine:** Advanced candidate matching using `Scikit-learn` TF-IDF and Cosine Similarity.
- **Blockchain Integrity:** Hash-linked vote storage ensuring a mathematically immutable ledger.
