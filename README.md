# Bot-Announcer


:mega: **Automation Goal**  
Set up a bot to **automatically post:**
- **Schedule messages** every **Monday at 18:00 UTC**  
- **Resource Drops** every **Friday at 18:00 UTC**  
…for **every cohort**.

---

:computer: **Codebase & Files**  
- [GitHub repo](https://github.com/lediau/Bot-Announcer)
- `.env` will be shared here (don’t push it)

---

:white_check_mark: **Weekly Requirements**

**Monday (Schedule Message)**  
→ Ensure the Notion page structure follows:  
- `h1` Sprint titles: `Sprint S (MONTH N – MONTH N)`  
- `h3` Week titles: `Week X` or `Weeks X–Y`

---

:bulb: **Future Improvements**
- :white_check_mark: Test across different cohorts
- :repeat: Convert Notion pages to Excel to reduce scraping bugs
- :white_check_mark: Add a confirmation step:  
  → Bot posts a preview in a private channel  
  → Waits for approval  
  → Then posts in public
