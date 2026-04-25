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
2. **Login:** Provide your username/email and password to access your dashboard.
3. **Security Locking:** If you enter the wrong password 5 times, your account will be locked for security. Contact an admin to unlock it.

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

### 4. Smart Features & Technology Breakdown

The Smart E-Voting System integrates advanced technologies to ensure a secure, intelligent, and user-centric voting experience.

### 4.1 Artificial Intelligence (AI)
*   **NLP Candidate Matching System**:
    *   **How it works**: Uses **TF-IDF (Term Frequency-Inverse Document Frequency)** and **Cosine Similarity** algorithms.
    *   **Logic**: It analyzes the candidate's manifesto (description and keywords) and compares them with the user's stated interests. It calculates a "Match Percentage" based on the linguistic overlap and thematic relevance.
    *   **Benefit**: Helps voters find candidates who align with their personal values and interests.

### 4.2 Machine Learning (ML)
*   **Voter Turnout Prediction**:
    *   **How it works**: Analyzes real-time voting velocity (votes per hour) and historical trends using **Linear Regression** logic.
    *   **Logic**: It calculates the current "momentum" of the election and predicts the final expected turnout and peak voting hours.
    *   **Benefit**: Helps administrators manage server load and understand engagement levels.
*   **Anomaly Detection (Security)**:
    *   **How it works**: Uses the **Isolation Forest** algorithm (Unsupervised Learning).
    *   **Logic**: It monitors the time interval between votes. If a sudden spike in voting occurs (e.g., 100 votes in 1 second), it flags this as an "Outlier" or "Bot-like" behavior and triggers a system alert.
    *   **Benefit**: Prevents automated bot attacks from manipulating results.

### 4.3 Internet of Behavior (IOB)
*   **Real-Time Engagement Monitoring**:
    *   **How it works**: Tracks user interactions, page dwell time, and "Bounce" points.
    *   **Logic**: The system monitors where users spend the most time (e.g., registration vs. voting). If users spend too long on a page without finishing, it identifies it as a "Bottleneck."
    *   **Benefit**: Allows administrators to optimize the user interface and simplify difficult steps to increase participation.

### 4.4 Behavioral Security & Blockchain
*   **Smart Risk Scoring**:
    *   **How it works**: A multi-factor risk engine that assigns a score (0-100) to every session.
    *   **Logic**: Factors include **IP Address changes**, **failed login attempts**, **late-night activity**, and **rapid page refreshes**.
    *   **Benefit**: Automatically flags compromised accounts or suspicious sessions for admin review.
*   **Blockchain Vote Integrity**:
    *   **How it works**: Each vote is treated as a "Block" in a chain.
    *   **Logic**: Every vote contains the **Hash** of the previous vote. If anyone attempts to modify a vote in the database, the "Chain" breaks, and the system immediately detects the tampering.
    *   **Benefit**: Guarantees that votes cannot be changed after they are cast.

### 4.5 Performance & Infrastructure
*   **Smart Caching**: Uses **Flask-Caching** (SimpleCache) to store expensive database queries and AI calculations for 60 seconds, ensuring the dashboard remains fast even under heavy traffic.

---

## 5. Performance & Technology
- **Caching Engine:** Uses `Flask-Caching` for instant load times across the dashboard and analytics.
- **AI Security:** Real-time anomaly detection using `Isolation Forest` algorithms.
- **NLP Engine:** Advanced candidate matching using `Scikit-learn` TF-IDF and Cosine Similarity.
- **Blockchain Integrity:** Hash-linked vote storage ensuring a mathematically immutable ledger.
